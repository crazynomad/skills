# Token 账单解读 · 成本基准与省钱依据

> 绿皮火车节目素材 + token-receipt skill 的知识底座。
> 数据快照:2026-06(burn.wang 本机 ccusage 实测)。所有 token 数经独立复算校验,
> 与 ccusage 对齐到 0.03% 以内;成本用 models.dev/LiteLLM 价格表,非真实账单。

## 1. 6 月真实画像($1,205.82)

### 按模型(单价 = $/百万 token:input / output / cache_write / cache_read)

| 模型 | 单价 | 花费 | 占比 | 备注 |
|---|---|---:|---:|---|
| claude-opus-4-8 | 5 / 25 / 6.25 / 0.5 | $946.22 | 78% | 主力 |
| claude-fable-5 | **10 / 50 / 12.5 / 1.0** | $219.45 | 18% | **最贵,opus 的 2×,且强制 extended thinking** |
| claude-opus-4-7 | 5 / 25 / 6.25 / 0.5 | $36.48 | 3% | |
| claude-haiku-4-5 | 1 / 5 / 1.25 / 0.1 | $2.51 | <1% | 256 次请求才 $2.5,性价比标杆 |
| claude-sonnet-4-6 | 3 / 15 / 3.75 / 0.3 | $1.17 | <1% | 几乎没用 |

### opus-4-8 成本如何构成(逐项相加 = $945.30,与 ccusage 一致)

| 类型 | token 数 | 占量 | 花费 | 占钱 |
|---|---:|---:|---:|---:|
| input | 1,490,052 | 0.1% | $7.45 | 0.8% |
| output | 4,817,009 | 0.4% | $120.43 | 12.7% |
| cache_write | 38,798,826 | 3.2% | $242.49 | 25.7% |
| **cache_read** | 1,149,862,364 | **96.2%** | $574.93 | **60.8%** |

### 集中度
- **项目**:`~/Github/greentrain/studio/main` 一个项目 = $703.55 = **58%**。
- opus-4-8 平均每次请求挂着 **~297k token** 的上下文(cache_read/请求)。
- opus-4-8 缓存读:写 = 29.7×(健康复用);opus-4-7 仅 5.9×(重写偏多,但金额小)。

## 2. 与官方基准对标

Anthropic 官方文档 [Manage costs effectively](https://code.claude.com/docs/en/costs)(企业部署实测):

| 官方基准 | 数值 |
|---|---|
| 平均 | **~$13 / 开发者 / 活跃日** |
| 平均 | **$150–250 / 开发者 / 月** |
| 90% 用户 | **< $30 / 活跃日** |
| 官方区间 | "$100 到 $1,200+/月,方差极大" |

**本机对标**:$1,205.82 / 17 活跃日 ≈ **$70.9/活跃日**
- ≈ 官方均值($13/日)的 **5.5×**
- ≈ 90 分位线($30/日)的 **2.4×**
- 月度几乎贴官方区间天花板($1,200+)

> 结论:**头部重度用户,非"正常用量"。** 官方 $150–250/月基准是默认 Sonnet 口径;
> 超出 5 倍主因是 Opus+Fable 的模型选择 —— 优化空间真实存在。

## 3. 省钱建议(按性价比排序)+ 官方背书

| # | 建议 | 预计可省 | 权威出处 |
|---|---|---|---|
| ① | **审 fable-5**:484 次 $219,同 token 换 opus 仅 $110;且 Fable 5 强制 extended thinking(按 output 计费) | ~$100+ | [costs 文档](https://code.claude.com/docs/en/costs):"Fable 5 无法关闭 extended thinking" |
| ② | **按难度分流,默认 Sonnet**,Opus 留给硬核推理,琐碎用 Haiku | ~$190/月 | [costs 文档](https://code.claude.com/docs/en/costs):"Sonnet 胜任大多数编码,Opus 留给复杂架构/多步推理";"简单 subagent 用 `model: haiku`" |
| ③ | **context 减肥**:任务间 `/clear`、长会话 `/compact`、定向读取不灌大文件 | ~$80–150/月 | [costs 文档](https://code.claude.com/docs/en/costs)"Reduce token usage"整节 |
| ④ | **会话内别换模型**(切模型让缓存失效,重付 1.25× 写) | 视习惯 | [Prompt caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching) |
| ⑤ | **火力集中在 studio/main**(占 58%) | —— | 本机数据 |

保守估算:①+②+③ 叠加可把月成本从 **$1,206 → $750–850(省 30%+)**,不牺牲效果。

## 4. 缓存经济学(官方)

来自 [Prompt caching — Claude API Docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching):

- cache read = **0.1× input(便宜 90%)**
- 5 分钟 cache write = 1.25× input;1 小时 = 2× input
- 官方明确把 **"agentic 工具调用"与"长对话"** 列为缓存最受益场景 → **Claude Code 里 cache_read 占 95% 是设计使然,正常。**
- 节目金句:6 月那 11.5 亿 cache_read,若无缓存按 input 收费要 **$5,749**,走缓存只花 **$575** —— 缓存替你省了 **~$5,174**(单 opus 一项)。

## 5. 信源

- [Manage costs effectively — Claude Code Docs(Anthropic 官方)](https://code.claude.com/docs/en/costs)
- [Prompt caching — Claude API Docs(Anthropic 官方)](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [Claude Model Selection Guide — SitePoint](https://www.sitepoint.com/claude-model-selection-framework/)
- [Claude Code Models: model selection — claudefa.st](https://claudefa.st/blog/models/model-selection)
- [Claude Code Pricing 2026 — CloudZero](https://www.cloudzero.com/blog/claude-code-pricing/)
