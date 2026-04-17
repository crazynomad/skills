// fix-html-for-pptx.js — 自动修 html2pptx 契约违规
//
// 解决的 2 条硬约束：
//   契约规则 3：<p>/<h1-6>/<ul>/<ol> 等文本元素不能有 background/border*/box-shadow
//   契约规则 4：<div> 不能直接含裸文本
//
// 修复策略：
//   对于 <p class="FOO">...</p>，如果 .FOO 定义里含 background/border*/box-shadow，
//   转成 <div class="FOO"><p>...</p></div>——外层 div 承载背景，内层 p 承载文字。
//
// class 匹配走"whitespace token"精确比对，不会把 `.shot` 匹进 `<p class="shot-no">`。
//
// 用法：
//   cd deck/
//   node tools/fix-html-for-pptx.js
//
// 幂等：多次运行只会处理新产生的违规，不会反复嵌套。

const fs = require('fs');
const path = require('path');

const SLIDES_DIR = path.resolve(__dirname, '../slides');
const files = fs.readdirSync(SLIDES_DIR)
  .filter(f => /^slide\d+\.html$/.test(f))
  .sort();

let fixedCount = 0;

for (const f of files) {
  const fp = path.join(SLIDES_DIR, f);
  let html = fs.readFileSync(fp, 'utf8');
  const before = html;

  const styleMatch = html.match(/<style>([\s\S]*?)<\/style>/);
  if (!styleMatch) continue;
  const cssBlock = styleMatch[1];

  // 扫 <style> 里所有含 background/border/box-shadow 的类名
  const classesToConvert = new Set();
  const ruleMatches = cssBlock.matchAll(/\.([a-zA-Z0-9_-]+)\s*\{([^}]*)\}/g);
  for (const m of ruleMatches) {
    const name = m[1];
    const body = m[2];
    if (
      /(^|;|\s)background\s*:/.test(body) ||
      /(^|;|\s)border(?:-left|-right|-top|-bottom)?\s*:/.test(body) ||
      /(^|;|\s)box-shadow\s*:/.test(body)
    ) {
      classesToConvert.add(name);
    }
  }

  // 把所有 <p class="..."> 中 class token 精确命中 classesToConvert 的，
  // 转成 <div class="..."><p>...</p></div>
  const converted = new Set();
  html = html.replace(
    /<p(\s[^>]*?)class="([^"]+)"([^>]*)>([\s\S]*?)<\/p>/g,
    (full, pre, classAttr, post, body) => {
      const tokens = classAttr.split(/\s+/).filter(Boolean);
      const hit = tokens.find(t => classesToConvert.has(t));
      if (!hit) return full;
      // 幂等性检查：如果 body 已经是单一 <p>...</p>，说明已修过，不再包一层
      if (/^\s*<p>[\s\S]*<\/p>\s*$/.test(body)) return full;
      converted.add(hit);
      return `<div${pre}class="${classAttr}"${post}><p>${body}</p></div>`;
    }
  );

  if (html !== before) {
    fs.writeFileSync(fp, html);
    fixedCount++;
    console.log(`  ${f}: ${[...converted].join(', ')}`);
  }
}

console.log(`\n${fixedCount} / ${files.length} file(s) changed`);
process.exit(0);
