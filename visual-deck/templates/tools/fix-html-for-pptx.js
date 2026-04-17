// fix-html-for-pptx.js — 自动修 html2pptx 契约违规
//
// 覆盖契约规则：
//   规则 3：<p>/<h1-6>/<ul>/<ol> 等文本元素不能有 background/border*/box-shadow
//   规则 4：<div> 不能直接含裸文本
//   规则 7：<div> 的直接子 <span> 文字在 PPTX 里会静默消失
//
// 修复策略：
//   规则 3：带 bg/border 的 <p class="FOO">...</p> → <div class="FOO"><p>...</p></div>
//   规则 7：仅含 <span> 子节点的 <div class="BAR"> → 把 top-level <span> 全换成 <p>，并加 .BAR p { margin: 0 } 样式
//
// class 匹配走"whitespace token"精确比对，不会把 .shot 匹进 <p class="shot-no">。
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

  // --- 规则 3 修复 ---
  const bgClasses = new Set();
  const ruleMatches = cssBlock.matchAll(/\.([a-zA-Z0-9_-]+)\s*\{([^}]*)\}/g);
  for (const m of ruleMatches) {
    const name = m[1];
    const body = m[2];
    if (
      /(^|;|\s)background\s*:/.test(body) ||
      /(^|;|\s)border(?:-left|-right|-top|-bottom)?\s*:/.test(body) ||
      /(^|;|\s)box-shadow\s*:/.test(body)
    ) {
      bgClasses.add(name);
    }
  }

  const convertedR3 = new Set();
  html = html.replace(
    /<p(\s[^>]*?)class="([^"]+)"([^>]*)>([\s\S]*?)<\/p>/g,
    (full, pre, classAttr, post, body) => {
      const tokens = classAttr.split(/\s+/).filter(Boolean);
      const hit = tokens.find(t => bgClasses.has(t));
      if (!hit) return full;
      if (/^\s*<p>[\s\S]*<\/p>\s*$/.test(body)) return full;
      convertedR3.add(hit);
      return `<div${pre}class="${classAttr}"${post}><p>${body}</p></div>`;
    }
  );

  // --- 规则 7 修复 ---
  // 只拿"直接子节点只有 span + whitespace"的 div（允许 span 内嵌 1 层 span）
  const spanTagToken = '<span(?:\\s[^>]*)?>(?:[^<]|<span(?:\\s[^>]*)?>[^<]*<\\/span>)*<\\/span>';
  const divOnlySpansRe = new RegExp(
    `<div(\\s[^>]*?)class="([^"]+)"([^>]*)>(\\s*(?:${spanTagToken}\\s*){2,})<\\/div>`,
    'g'
  );
  const convertedR7 = new Set();
  html = html.replace(divOnlySpansRe, (full, pre, classAttr, post, body) => {
    // 把每个 top-level <span ...>...</span> 转成 <p ...>...</p>
    const newBody = body.replace(
      new RegExp(spanTagToken, 'g'),
      (spanFull) => {
        // 只改最外层标签
        const openEnd = spanFull.indexOf('>') + 1;
        const open = spanFull.slice(0, openEnd);
        const inner = spanFull.slice(openEnd, -'</span>'.length);
        const newOpen = open.replace(/^<span/, '<p').replace(/\s*\/?>$/, '>');
        return `${newOpen}${inner}</p>`;
      }
    );
    const mainClass = classAttr.split(/\s+/)[0];
    convertedR7.add(mainClass);
    return `<div${pre}class="${classAttr}"${post}>${newBody}</div>`;
  });

  // 为规则 7 修复的类注入 "ClASS p { margin: 0 }" 规则（如果还没有）
  if (convertedR7.size > 0) {
    const styleStart = html.indexOf('<style>') + '<style>'.length;
    const styleEnd = html.indexOf('</style>');
    let newStyle = html.slice(styleStart, styleEnd);
    for (const cls of convertedR7) {
      const marker = `.${cls} p { margin: 0`;
      if (!newStyle.includes(marker)) {
        newStyle = newStyle + `\n.${cls} p { margin: 0; }`;
      }
    }
    html = html.slice(0, styleStart) + newStyle + html.slice(styleEnd);
  }

  if (html !== before) {
    fs.writeFileSync(fp, html);
    fixedCount++;
    const r3Str = convertedR3.size ? `R3[${[...convertedR3].join(', ')}]` : '';
    const r7Str = convertedR7.size ? `R7[${[...convertedR7].join(', ')}]` : '';
    console.log(`  ${f}: ${[r3Str, r7Str].filter(Boolean).join('  ')}`);
  }
}

console.log(`\n${fixedCount} / ${files.length} file(s) changed`);
process.exit(0);
