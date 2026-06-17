#!/usr/bin/env python3
"""Generate a receipt-style token-usage bill from ccusage data.

Pulls real usage from the `ccusage` CLI (JSON), then renders a printer-receipt
styled HTML and screenshots it to a crisp PNG via headless Google Chrome +
ImageMagick trim. Designed as 节目 (show) material for the 绿皮火车 channel.

Stdlib only. See SKILL.md for usage.
"""
from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import os
import shutil
import subprocess
import sys
import tempfile

# ---------------------------------------------------------------------------
# ccusage data access
# ---------------------------------------------------------------------------

def run_ccusage(period: str, agent: str | None) -> dict:
    """Run `ccusage [agent] <period> --json` and return parsed JSON.

    `modelBreakdowns` is always present in ccusage output, so we don't need
    --breakdown (which isn't accepted by every subcommand).
    """
    cmd = ["ccusage"]
    if agent and agent != "all":
        cmd.append(agent)
    cmd += [period, "--json"]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, check=True).stdout
    except FileNotFoundError:
        sys.exit("error: `ccusage` not found on PATH. Install it first (npm i -g ccusage).")
    except subprocess.CalledProcessError as e:
        sys.exit(f"error: ccusage failed: {e.stderr.strip() or e}")
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        sys.exit("error: ccusage did not return JSON. Try a newer ccusage.")


def rows_of(data: dict, period: str) -> list[dict]:
    """ccusage nests the list under the period name (daily/weekly/monthly)."""
    return data.get(period) or data.get("data") or []


# ---------------------------------------------------------------------------
# formatting helpers
# ---------------------------------------------------------------------------

def commas(n: int) -> str:
    return f"{int(round(n)):,}"


def human_tokens(n: float) -> str:
    n = float(n)
    if n >= 1_000_000:
        return f"{n / 1_000_000:.2f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}k"
    return str(int(round(n)))


def money(n: float) -> str:
    return f"${n:,.2f}"


def pct(part: float, whole: float) -> float:
    return (part / whole * 100.0) if whole else 0.0


# ---------------------------------------------------------------------------
# data shaping
# ---------------------------------------------------------------------------

TOKEN_KINDS = [
    ("inputTokens", "Input", "#1f6f5c"),
    ("outputTokens", "Output", "#d98c3f"),
    ("cacheCreationTokens", "Cache write", "#6b8fb5"),
    ("cacheReadTokens", "Cache read", "#b0a98f"),
]


def week_range(period_start: str) -> tuple[dt.date, dt.date]:
    start = dt.date.fromisoformat(period_start)
    return start, start + dt.timedelta(days=6)


def daily_rows_for(target: dict, period: str, agent: str | None) -> list[dict]:
    """Pull per-day rows that fall inside the chosen month/week period."""
    daily = rows_of(run_ccusage("daily", agent), "daily")
    if period == "monthly":
        prefix = target["period"]  # YYYY-MM
        return [r for r in daily if str(r.get("period", "")).startswith(prefix)]
    if period == "weekly":
        start, end = week_range(target["period"])
        out = []
        for r in daily:
            try:
                d = dt.date.fromisoformat(r["period"])
            except (ValueError, KeyError):
                continue
            if start <= d <= end:
                out.append(r)
        return out
    return [target]


def pick_target(rows: list[dict], which: str) -> dict:
    if not rows:
        sys.exit("error: ccusage returned no usage data for that period.")
    if which == "latest":
        return rows[-1]
    for r in rows:
        if str(r.get("period")) == which:
            return r
    avail = ", ".join(str(r.get("period")) for r in rows)
    sys.exit(f"error: period '{which}' not found. Available: {avail}")


# ---------------------------------------------------------------------------
# HTML rendering
# ---------------------------------------------------------------------------

TRAIN = r"""        ~  ~
       ~  o
      .===================.
   .--|  []   []   []   []|--.
   |  |___________________|  |
  _|__|=o=============o====|__|_
 |____(O)___________(O)_______|
    `--(o)--'     `--(o)--'"""


def esc(s: str) -> str:
    return html.escape(str(s))


def leader(label: str, value: str, *, strong=False, dim=False) -> str:
    vcls = "val strong" if strong else "val"
    lcls = "label dim" if dim else "label"
    return (
        f'<div class="line"><span class="{lcls}">{esc(label)}</span>'
        f'<span class="dots"></span><span class="{vcls}">{esc(value)}</span></div>'
    )


def token_mix_bar(target: dict) -> str:
    total = sum(target.get(k, 0) for k, _, _ in TOKEN_KINDS) or 1
    segs, legend = [], []
    for key, name, color in TOKEN_KINDS:
        v = target.get(key, 0)
        p = pct(v, total)
        if p > 0:
            segs.append(f'<span style="width:{p:.3f}%;background:{color}"></span>')
        legend.append(
            f'<div class="leg-item"><span class="sw" style="background:{color}"></span>'
            f'{esc(name)} <b>{p:.1f}%</b></div>'
        )
    return (
        '<div class="mixbar">' + "".join(segs) + "</div>"
        '<div class="legend">' + "".join(legend) + "</div>"
    )


def model_table(target: dict) -> str:
    breakdowns = sorted(
        target.get("modelBreakdowns", []),
        key=lambda m: m.get("cost", 0),
        reverse=True,
    )
    total_cost = target.get("totalCost", 0) or 1
    rows = []
    for m in breakdowns:
        name = m.get("modelName", "?")
        c = m.get("cost", 0)
        share = pct(c, total_cost)
        toks = (
            f"in {human_tokens(m.get('inputTokens', 0))} · "
            f"out {human_tokens(m.get('outputTokens', 0))} · "
            f"cache {human_tokens(m.get('cacheCreationTokens', 0) + m.get('cacheReadTokens', 0))}"
        )
        rows.append(
            f'<div class="mrow">'
            f'<div class="mhead"><span class="mname">{esc(name)}</span>'
            f'<span class="mcost">{esc(money(c))}</span></div>'
            f'<div class="msub">{esc(toks)}</div>'
            f'<div class="mbar"><span style="width:{share:.2f}%"></span></div>'
            f'<div class="mshare">{share:.1f}% of spend</div>'
            f"</div>"
        )
    return "".join(rows)


def daily_section(days: list[dict]) -> str:
    if not days:
        return ""
    days = sorted(days, key=lambda r: r.get("period", ""))
    maxc = max((d.get("totalCost", 0) for d in days), default=0) or 1
    rows = []
    for d in days:
        label = str(d.get("period", ""))[5:]  # MM-DD
        c = d.get("totalCost", 0)
        w = pct(c, maxc)
        rows.append(
            f'<div class="drow"><span class="dday">{esc(label)}</span>'
            f'<span class="dtrack"><span class="dfill" style="width:{w:.2f}%"></span></span>'
            f'<span class="dval">{esc(money(c))}</span></div>'
        )
    return (
        '<div class="sect-title">DAILY SPEND · 按天</div>'
        '<div class="daily">' + "".join(rows) + "</div>"
    )


YOUTUBE_URL = "https://www.youtube.com/channel/UCJhUtNsR5pvU_gWWkxxUXUQ"  # 绿皮火车


def qr_svg(url: str) -> str:
    """Inline a crisp SVG QR code for `url` via the qrencode CLI."""
    qrenc = shutil.which("qrencode")
    if not qrenc:
        return '<div class="qr-cap">[install qrencode to embed the channel QR]</div>'
    try:
        svg = subprocess.run([qrenc, "-t", "SVG", "-m", "1", "-o", "-", url],
                             capture_output=True, text=True, check=True).stdout
    except subprocess.CalledProcessError:
        return '<div class="qr-cap">[QR generation failed]</div>'
    # strip xml prolog / doctype so the SVG inlines cleanly into HTML
    body = "\n".join(l for l in svg.splitlines()
                     if not l.lstrip().startswith(("<?xml", "<!DOCTYPE")))
    return f'<div class="qr">{body}</div>'


def build_html(target, days, *, period, agent, customer, totals_all, youtube) -> str:
    t = target
    tot_tokens = t.get("totalTokens", 0)
    tot_cost = t.get("totalCost", 0)
    models = t.get("modelsUsed", [])
    agents = (t.get("metadata", {}) or {}).get("agents", []) or ([agent] if agent else ["all"])
    period_label = t.get("period", "")
    if period == "weekly":
        s, e = week_range(period_label)
        period_label = f"{s.isoformat()} → {e.isoformat()}"
    kind = {"monthly": "MONTHLY", "weekly": "WEEKLY", "daily": "DAILY"}.get(period, period.upper())
    n_days = len([d for d in days if d.get("totalCost", 0) > 0]) or len(days)
    today = dt.date.today().isoformat()

    usage = "".join([
        leader("Input tokens", commas(t.get("inputTokens", 0))),
        leader("Output tokens", commas(t.get("outputTokens", 0))),
        leader("Cache write", commas(t.get("cacheCreationTokens", 0))),
        leader("Cache read", commas(t.get("cacheReadTokens", 0))),
        leader("Total tokens", commas(tot_tokens), strong=True),
    ])
    meta = "".join([
        leader("Period", period_label),
        leader("Billing cycle", kind),
        leader("Agents", ", ".join(agents)),
        leader("Models", str(len(models))),
        leader("Active days", str(n_days)),
        leader("Customer", customer),
        leader("Issued", today),
    ])

    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
:root {{
  --ink:#1b1b1b; --soft:#6f6a5c; --paper:#f6f4ec; --line:#cfc9b8;
  --accent:#1f6f5c; --page:#e8e6df;
}}
* {{ box-sizing:border-box; }}
html,body {{ margin:0; background:var(--page); }}
.wrap {{ padding:48px; display:inline-block; }}
.receipt {{
  width:560px; background:var(--paper); color:var(--ink);
  font-family:"Menlo","SF Mono","Cascadia Code",ui-monospace,monospace;
  font-size:14px; line-height:1.55; padding:36px 34px 30px;
  box-shadow:0 18px 50px rgba(0,0,0,.18);
  position:relative;
}}
.edge {{ height:10px; background:
  radial-gradient(circle at 6px -2px, transparent 6px, var(--paper) 6px) repeat-x;
  background-size:12px 10px; }}
.edge.top {{ margin:-36px -34px 18px; background-position:0 0;
  background:radial-gradient(circle at 6px 10px, var(--page) 6px, var(--paper) 7px) repeat-x;
  background-size:12px 12px; height:12px; }}
.edge.bot {{ margin:18px -34px -30px;
  background:radial-gradient(circle at 6px 2px, var(--page) 6px, var(--paper) 7px) repeat-x;
  background-size:12px 12px; height:12px; }}
pre.train {{ font-size:11px; line-height:1.15; text-align:center; margin:0 0 10px;
  color:var(--ink); white-space:pre; }}
.brand {{ text-align:center; font-weight:700; letter-spacing:3px; font-size:16px; }}
.sub {{ text-align:center; color:var(--soft); letter-spacing:2px; font-size:11px;
  margin-top:3px; }}
.hr {{ border-top:1px dashed var(--line); margin:16px 0; }}
.hr.solid {{ border-top:2px solid var(--ink); }}
.line {{ display:flex; align-items:baseline; margin:2px 0; }}
.line .label {{ white-space:nowrap; }}
.line .label.dim {{ color:var(--soft); }}
.line .dots {{ flex:1; border-bottom:1px dotted var(--line); margin:0 7px;
  transform:translateY(-4px); }}
.line .val {{ white-space:nowrap; }}
.line .val.strong {{ font-weight:700; }}
.sect-title {{ font-weight:700; letter-spacing:2px; font-size:12px; margin:4px 0 8px; }}
.mixbar {{ display:flex; height:16px; border-radius:3px; overflow:hidden;
  border:1px solid var(--line); }}
.mixbar span {{ display:block; height:100%; }}
.legend {{ display:flex; flex-wrap:wrap; gap:6px 14px; margin-top:8px; font-size:11px;
  color:var(--soft); }}
.leg-item {{ display:flex; align-items:center; }}
.leg-item b {{ color:var(--ink); margin-left:4px; }}
.sw {{ width:10px; height:10px; border-radius:2px; margin-right:5px; display:inline-block; }}
.mrow {{ margin:10px 0; }}
.mhead {{ display:flex; justify-content:space-between; font-weight:700; }}
.msub {{ color:var(--soft); font-size:11px; margin:1px 0 4px; }}
.mbar {{ height:7px; background:#e4dfcf; border-radius:4px; overflow:hidden; }}
.mbar span {{ display:block; height:100%; background:var(--accent); }}
.mshare {{ font-size:10px; color:var(--soft); margin-top:2px; text-align:right; }}
.daily {{ margin-top:4px; }}
.drow {{ display:flex; align-items:center; margin:3px 0; font-size:12px; }}
.dday {{ width:48px; color:var(--soft); }}
.dtrack {{ flex:1; height:8px; background:#e4dfcf; border-radius:4px;
  margin:0 8px; overflow:hidden; }}
.dfill {{ display:block; height:100%; background:var(--accent); }}
.dval {{ width:72px; text-align:right; }}
.total {{ display:flex; justify-content:space-between; align-items:baseline;
  font-weight:800; font-size:24px; margin:6px 0; }}
.total .amt {{ color:var(--accent); }}
.foot {{ text-align:center; color:var(--soft); font-size:11px; margin-top:8px; }}
.foot .thanks {{ color:var(--ink); font-weight:700; font-size:13px; margin:10px 0 4px;
  letter-spacing:1px; }}
.qr {{ width:118px; margin:16px auto 5px; }}
.qr svg {{ width:100%; height:auto; display:block; image-rendering:pixelated; }}
.qr-cap {{ font-size:10px; color:var(--soft); letter-spacing:1px; }}
.disc {{ font-size:9.5px; color:#9a9486; line-height:1.5; margin-top:8px; }}
</style></head><body><div class="wrap"><div class="receipt">
<div class="edge top"></div>
<pre class="train">{esc(TRAIN)}</pre>
<div class="brand">绿皮火车 · TOKEN RECEIPT</div>
<div class="sub">GREEN TRAIN EXPRESS · 代币消耗收银台</div>
<div class="hr"></div>
{meta}
<div class="hr"></div>
<div class="sect-title">TOKEN USAGE · 用量</div>
{usage}
<div class="hr"></div>
<div class="sect-title">TOKEN MIX · 类型分布</div>
{token_mix_bar(t)}
<div class="hr"></div>
<div class="sect-title">COST BY MODEL · 分模型花费</div>
{model_table(t)}
<div class="hr"></div>
{daily_section(days)}
<div class="hr solid"></div>
<div class="total"><span>TOTAL · 合计</span><span class="amt">{esc(money(tot_cost))}</span></div>
<div class="hr solid"></div>
<div class="foot">
  {qr_svg(youtube)}
  <div class="qr-cap">▶ 绿皮火车 · YouTube · 扫码上车</div>
  <div>{esc(period_label)}</div>
  <div class="disc">*token counts are read from local logs via ccusage (essentially exact);
  costs use the models.dev/LiteLLM price table, not a real billing API.
  cache-read tokens are cheap per token (~1/10 of input) yet, at this volume, can still be
  the largest line — caching saves ~10x vs paying full input price.<br>
  generated by 绿皮火车 token-receipt skill</div>
</div>
<div class="edge bot"></div>
</div></div></body></html>"""


# ---------------------------------------------------------------------------
# rendering to PNG
# ---------------------------------------------------------------------------

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


def render_png(html_path: str, out_path: str, scale: int) -> None:
    if not os.path.exists(CHROME):
        sys.exit(f"error: Google Chrome not found at {CHROME}; use --html-only.")
    raw = out_path + ".raw.png"
    cmd = [
        CHROME, "--headless=new", "--hide-scrollbars",
        f"--force-device-scale-factor={scale}",
        "--window-size=720,4000",
        "--default-background-color=e8e6dfff",
        f"--screenshot={raw}", f"file://{html_path}",
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if not os.path.exists(raw):
        sys.exit(f"error: Chrome screenshot failed.\n{r.stderr[-800:]}")
    magick = shutil.which("magick") or shutil.which("convert")
    if magick:
        subprocess.run(
            [magick, raw, "-trim", "+repage",
             "-bordercolor", "#e8e6df", "-border", "36", out_path],
            check=False,
        )
        if os.path.exists(out_path):
            os.remove(raw)
            return
    os.replace(raw, out_path)


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser(description="Generate a token-usage receipt PNG from ccusage.")
    ap.add_argument("--period", choices=["month", "week"], default="month")
    ap.add_argument("--which", default="latest",
                    help="latest | YYYY-MM (month) | YYYY-MM-DD week-start (week)")
    ap.add_argument("--agent", default=None,
                    help="ccusage agent (claude, codex, opencode, pi, ...); default all agents")
    ap.add_argument("--customer", default=None, help="name printed on the receipt")
    ap.add_argument("--youtube", default=YOUTUBE_URL, help="URL encoded in the footer QR code")
    ap.add_argument("--out", default=None, help="output PNG path")
    ap.add_argument("--scale", type=int, default=2, help="device scale factor (2 = retina)")
    ap.add_argument("--html-only", action="store_true", help="emit HTML, skip screenshot")
    args = ap.parse_args()

    period = {"month": "monthly", "week": "weekly"}[args.period]
    data = run_ccusage(period, args.agent)
    rows = rows_of(data, period)
    target = pick_target(rows, args.which)
    days = daily_rows_for(target, period, args.agent)
    customer = args.customer or os.environ.get("RECEIPT_CUSTOMER") or "Burn Wang"

    page = build_html(target, days, period=period, agent=args.agent,
                      customer=customer, totals_all=data.get("totals"),
                      youtube=args.youtube)

    out = args.out or os.path.expanduser(
        f"~/Desktop/token-receipt-{target.get('period', 'latest')}.png")
    out = os.path.expanduser(out)

    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as f:
        f.write(page)
        html_path = f.name

    if args.html_only:
        html_out = out.rsplit(".", 1)[0] + ".html"
        shutil.copy(html_path, html_out)
        print(html_out)
        return

    render_png(html_path, out, args.scale)
    os.unlink(html_path)
    print(out)


if __name__ == "__main__":
    main()
