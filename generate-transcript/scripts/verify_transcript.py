#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""verify_transcript.py — 转录产出的自动验证门。

为什么存在: whisper(尤其 large-v3) 在长段语音/静音/音乐上会退化成"同一句无限
复读"的幻觉循环; 也可能整段漏转。这两类错误肉眼扫一遍开头根本看不出来 —— 必须有
一道机器验证门拦在"宣布完成"之前。本脚本只用 whisper 自己吐的 JSON 元数据(无需额
外模型)做三类检查, 给出 PASS / WARN / FAIL 与证据。

检查项:
  1) 覆盖率缺口 (truncation/loss): 音频时长 vs 最后一条字幕结束时间。
     缺口过大 => 可能整段漏转 / 被错误截断。
  2) 重复循环 (hallucination loop): 连续相同文本 >= N 条, 或某条规范化文本
     占全部 segment 比例过高 => 复读幻觉。给出时间区间。
  3) 低置信聚集: avg_logprob 过低 / compression_ratio 过高(whisper 内置的
     重复度指标) / no_speech_prob 过高 的 segment 聚集 => 该段不可信。

用法:
  verify_transcript.py <transcript.json|transcript.srt> [--audio AUDIO] \
      [--reference REF.srt] [--json]

  --audio     原始音频/视频, 用 ffprobe 取时长做覆盖率检查(强烈建议传)。
  --reference 已知正确的参考 SRT; 传了则额外比对覆盖时长 (ground-truth gate)。
  --json      以 JSON 打印机器可读结论(供脚本消费)。

退出码: 0=PASS, 0=WARN(打印警告但不挡), 2=FAIL。CI/脚本可据此 gate。
"""
import argparse
import json
import re
import subprocess
import sys
from collections import Counter

# ---- 阈值 (经验值, 可按需调) ----
LOOP_CONSECUTIVE = 4          # 连续相同文本 >= 此数 => 循环
LOOP_FRACTION = 0.04          # 单条规范化文本占比 > 此值 => 循环
COVERAGE_GAP_ABS = 20.0       # 末尾覆盖缺口 > 此秒数(且超相对阈值) => 疑似漏转
COVERAGE_GAP_REL = 0.03       # 且缺口 > 总时长的此比例
INTERNAL_GAP = 25.0           # 相邻字幕间静默 > 此秒数 => 提示(可能漏转一段)
LOGPROB_FLOOR = -1.0          # avg_logprob 低于此 => 低置信
COMPRESSION_CEIL = 2.4        # compression_ratio 高于此 => whisper 判定文本过度重复
NOSPEECH_CEIL = 0.6           # no_speech_prob 高于此 => 该段大概率无语音


def norm(t: str) -> str:
    """规范化文本用于重复比对: 去标点/空白, 统一大小写。"""
    return re.sub(r"[\s，。、！？!?.,;:：；…\"'“”‘’()（）\-—]+", "", t).lower()


def parse_ts(s: str) -> float:
    s = s.strip().replace(".", ",")
    h, m, rest = s.split(":")
    sec, ms = rest.split(",")
    return int(h) * 3600 + int(m) * 60 + int(sec) + int(ms) / 1000


def load_segments(path: str):
    """返回 [{start,end,text, avg_logprob?, compression_ratio?, no_speech_prob?}]。"""
    if path.lower().endswith(".json"):
        d = json.load(open(path, encoding="utf-8-sig"))
        segs = d.get("segments", [])
        return [{
            "start": s["start"], "end": s["end"], "text": s.get("text", "").strip(),
            "avg_logprob": s.get("avg_logprob"),
            "compression_ratio": s.get("compression_ratio"),
            "no_speech_prob": s.get("no_speech_prob"),
        } for s in segs], True
    # SRT 回退 (无置信度元数据)
    raw = open(path, encoding="utf-8-sig").read()
    out = []
    for b in re.split(r"\n\s*\n", raw.strip()):
        L = [x for x in b.splitlines() if x.strip()]
        if len(L) < 2 or "-->" not in L[1]:
            continue
        a, e = L[1].split("-->")
        out.append({"start": parse_ts(a), "end": parse_ts(e),
                    "text": "".join(L[2:]).strip(),
                    "avg_logprob": None, "compression_ratio": None, "no_speech_prob": None})
    return out, False


def audio_duration(path: str):
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", path],
            capture_output=True, text=True, check=True)
        return float(r.stdout.strip())
    except Exception:
        return None


def fmt(t: float) -> str:
    h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return f"{h:02d}:{m:02d}:{s:05.2f}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("transcript")
    ap.add_argument("--audio")
    ap.add_argument("--reference")
    ap.add_argument("--json", action="store_true", dest="as_json")
    args = ap.parse_args()

    segs, has_meta = load_segments(args.transcript)
    findings = []  # (level, code, message)  level in {FAIL,WARN,INFO}

    if not segs:
        print("FAIL: 转录为空, 没有任何 segment。")
        sys.exit(2)

    n = len(segs)
    last_end = max(s["end"] for s in segs)
    first_start = min(s["start"] for s in segs)

    # ---- 1) 覆盖率缺口 ----
    dur = audio_duration(args.audio) if args.audio else None
    if dur:
        tail_gap = dur - last_end
        if tail_gap > COVERAGE_GAP_ABS and tail_gap > COVERAGE_GAP_REL * dur:
            findings.append(("FAIL", "coverage-tail",
                f"末尾缺口 {tail_gap:.0f}s: 音频时长 {fmt(dur)}, 但字幕在 {fmt(last_end)} 就结束 "
                f"=> 疑似漏转/被错误截断了结尾。"))
        if first_start > COVERAGE_GAP_ABS:
            findings.append(("WARN", "coverage-head",
                f"开头缺口 {first_start:.0f}s: 首条字幕在 {fmt(first_start)} 才出现。"))

    # 内部大静默 (可能整段漏转)
    prev = None
    for s in sorted(segs, key=lambda x: x["start"]):
        if prev is not None and s["start"] - prev > INTERNAL_GAP:
            findings.append(("INFO", "coverage-gap",
                f"中间有 {s['start']-prev:.0f}s 静默: {fmt(prev)} → {fmt(s['start'])} (可能是停顿, 也可能漏转)。"))
        prev = max(prev, s["end"]) if prev is not None else s["end"]

    # ---- 2) 重复循环 ----
    normed = [norm(s["text"]) for s in segs]
    # 2a 连续相同
    run_start = 0
    i = 1
    worst_run = (0, 0, 0)  # (len, idx_start, idx_end)
    while i <= n:
        if i < n and normed[i] and normed[i] == normed[run_start]:
            i += 1
            continue
        run_len = i - run_start
        if normed[run_start] and run_len > worst_run[0]:
            worst_run = (run_len, run_start, i - 1)
        run_start = i
        i += 1
    if worst_run[0] >= LOOP_CONSECUTIVE:
        a, b = worst_run[1], worst_run[2]
        findings.append(("FAIL", "loop-consecutive",
            f"重复循环: 同一句连续出现 {worst_run[0]} 次 "
            f"({fmt(segs[a]['start'])} → {fmt(segs[b]['end'])}) => 复读幻觉。"
            f" 内容: 「{segs[a]['text'][:30]}」"))
    # 2b 高占比
    cnt = Counter(t for t in normed if t)
    if cnt:
        text, c = cnt.most_common(1)[0]
        frac = c / n
        if c >= LOOP_CONSECUTIVE and frac > LOOP_FRACTION:
            sample = next(s["text"] for s in segs if norm(s["text"]) == text)
            findings.append(("FAIL", "loop-fraction",
                f"重复循环: 同一句占全部 {n} 条的 {frac*100:.0f}% ({c} 次) => 复读幻觉。"
                f" 内容: 「{sample[:30]}」"))

    # ---- 3) 低置信聚集 (仅 JSON 有元数据) ----
    if has_meta:
        bad = [s for s in segs if (s["compression_ratio"] or 0) > COMPRESSION_CEIL]
        if bad:
            worst = max(bad, key=lambda s: s["compression_ratio"])
            findings.append(("WARN", "compression",
                f"{len(bad)} 条 compression_ratio > {COMPRESSION_CEIL} (whisper 自判文本过度重复), "
                f"最高 {worst['compression_ratio']:.1f} @ {fmt(worst['start'])}。"))
        lowp = [s for s in segs if s["avg_logprob"] is not None and s["avg_logprob"] < LOGPROB_FLOOR]
        if lowp:
            findings.append(("WARN", "logprob",
                f"{len(lowp)} 条 avg_logprob < {LOGPROB_FLOOR} (低置信)。"))

    # ---- 4) 参考对照 (ground truth) ----
    if args.reference:
        ref, _ = load_segments(args.reference)
        if ref:
            ref_end = max(s["end"] for s in ref)
            delta = ref_end - last_end
            if abs(delta) > COVERAGE_GAP_ABS:
                lvl = "FAIL" if delta > 0 else "WARN"
                findings.append((lvl, "reference",
                    f"与参考 SRT 覆盖时长差 {delta:+.0f}s: 参考到 {fmt(ref_end)}, 本次到 {fmt(last_end)}"
                    + (" => 本次可能漏了结尾。" if delta > 0 else " => 本次比参考还长, 检查是否尾部幻觉。")))

    # ---- 汇总 ----
    has_fail = any(f[0] == "FAIL" for f in findings)
    has_warn = any(f[0] == "WARN" for f in findings)
    verdict = "FAIL" if has_fail else ("WARN" if has_warn else "PASS")

    if args.as_json:
        print(json.dumps({
            "verdict": verdict, "segments": n,
            "covered": [first_start, last_end], "audio_duration": dur,
            "findings": [{"level": l, "code": c, "message": m} for l, c, m in findings],
        }, ensure_ascii=False, indent=2))
    else:
        icon = {"PASS": "✅", "WARN": "⚠️", "FAIL": "❌"}[verdict]
        print(f"{icon} 验证结论: {verdict}  ({n} 条字幕, 覆盖 {fmt(first_start)} → {fmt(last_end)}"
              + (f", 音频 {fmt(dur)}" if dur else "") + ")")
        if not findings:
            print("   无异常。")
        for lvl, code, msg in sorted(findings, key=lambda x: {"FAIL": 0, "WARN": 1, "INFO": 2}[x[0]]):
            tag = {"FAIL": "❌", "WARN": "⚠️ ", "INFO": "ℹ️ "}[lvl]
            print(f"   {tag} [{code}] {msg}")
        if has_fail:
            print("\n   => 不要直接交付。修复(换 turbo / 去尾部静音 / 人工核对该段)后重验。")

    sys.exit(2 if has_fail else 0)


if __name__ == "__main__":
    main()
