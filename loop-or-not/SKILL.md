---
name: loop-or-not
description: Decide whether a task in the current project is worth running as an agent loop. Analyzes the repo for evidence first (tests/CI/bench scripts = available verifiers; issue+PR queues = recurring work; module boundaries), then interviews the user one question at a time on the genuine decisions, and returns one of three verdicts — don't loop (stay in the loop yourself), timer loop (/loop, /schedule), or goal loop (/goal) — with cited evidence and, when looping is warranted, a drafted four-part contract (goal / verification / boundary / stop) bound to real commands found in the repo. Recommending NO loop is a first-class outcome. Use when the user asks 值不值得 loop / should I loop this / 要不要上 /goal / 这个活能不能挂个循环自动跑, or wants to apply loop engineering to a project.
version: 0.1.0
---

# loop-or-not — 「值不值得 loop」判断尺

对一个具体的活给出三叉裁决:**不 loop(你留圈里)/ 定时器 loop(/loop、/schedule)/ goal loop(/goal)**,并附证据;裁决为 loop 时,草拟一份绑定真实命令的契约。

设计出处:判断尺与三叉出口来自绿皮火车 EP14《Loop Engineering》(核心两问:这活做没做对,**谁说了算**?如果是你说了算,**你的判断写得下来吗**?);面试机制借自 [mattpocock/skills 的 grilling](https://github.com/mattpocock/skills)(事实查库、决策问人、一次一问、每问带推荐答案);判据与 Claude Code 官方三问同构(验证写得出来吗/目标够清晰吗/活是否按节奏出现),与 OpenAI goals 教程的「clear finish line, uncertain path」同构。

## 铁律

1. **「不 loop」是一等公民裁决**——本 skill 的价值有一半在劝退。不夸大 loop 的收益,不为了凑出「可以 loop」的结论降低验收门槛。
2. **事实查库,决策问人**:能从项目里查到的(测试/CI/队列/边界),不许问用户;属于用户的决策(什么算做完/风险口味/绝不外包什么),不许替答。
3. **一次只问一个问题**,附推荐答案,等回答再问下一个。
4. **证据必须具体**:文件路径、命令名、数字。禁止「这个项目看起来适合 loop」这类空话。
5. 裁决是**证据+建议**,最后一锤是用户的:「谁说了算/写得下来吗」两问必须由用户亲口确认——skill 的职责是把这两问逼到用户面前,带着证据。

## 流程

### 第 0 步 · 任务陈述

用户一句话说清想 loop 的活。若用户只问「这个项目适不适合 loop」而没有具体任务:先做第 1 步勘察,再**从队列证据里提名候选任务**(如「你有 23 个无标签 issue,backlog 整理是个候选」),不凭空发明任务。

### 第 1 步 · 事实勘察(查库,不问人)

产出一张证据表,三个方向:

**A. 裁判存量**(决定 goal 支可行性):
- 查 package.json / Makefile / justfile 的 test / lint / typecheck / build / bench 脚本;CI 配置(`.github/workflows` 等);现成的测量脚本。
- **试跑最像验收的那条命令**,确认真的能跑;红的裁判也是裁判,如实记录现状。
- 按硬度分级记录:确定性命令(测试/编译/数字阈值)> 半确定(lint/覆盖率)> 只有模型打分 > 无裁判。

**B. 队列存量**(决定定时器支可行性):
- `gh issue list` / `gh pr list` 的数量与标签卫生;CI 红的频率;TODO/FIXME 密度;依赖过期情况。
- 判据:这个活是否**重复出现且每次同构**。一次性的活不配定时器。

**C. 边界可切性**:
- 模块结构能否支撑「只许动 X」条款;有无分支保护、合并测试门;git 卫生。

非代码项目(写作/研究/运营):承认可查的东西少,退化为面试为主,并在裁决书里写明「证据薄,裁决主要依据你的回答」——不假装对什么项目都同样灵。

### 第 2 步 · 面试(决策,一次一问)

只问查不到的。题库按需取,通常 3–5 问收工,每问基于第 1 步证据给推荐答案:

1. 这活做没做对,**谁说了算**?(你 / 测试 / 数字 / 用户 / 时间)
2. 如果是你说了算——**你的判断写得下来吗**?请当场写一句给我看。
3. 验收里哪些判断你**绝不外包**?(方向 / 品味 / 要担责任的决定)
4. 预算和刹车的口味?(轮数上限 / token / 时限)
5. (定时器支)这活多久出现一次?错过一轮的代价是什么?

### 第 3 步 · 裁决书

格式固定:

```
裁决:不 loop / 定时器 loop(/loop /schedule)/ goal loop(/goal)
证据:<引用第 1 步的具体发现:路径、命令、数字>
理由:<对照下方三叉判据>
风险与前提:<诚实写:裁判硬度等级、边界弱点、证据薄的地方>
```

三叉判据:

- **判断交不出去**(方向/品味/责任),或验收写不下来,或没有裁判且不值得先造 → **不 loop,你留圈里**。可附「先造裁判」路线:先补测试/测量脚本,裁判有了再回来跑一次本 skill。
- **活重复出现、每次同构、裁判现成** → **定时器 loop**。
- **终点清晰、路径不明、验收能绑到确定性命令** → **goal loop**。

边界情况处置:
- 裁判只有「模型打分」可用 → 降级警告:模型打分不能冒充确定性判断,只可做参考裁判,不可做唯一裁判。
- 想 loop 的活其实一次就能干完 → 直接干,别造循环。
- 队列存在但一周不满一轮 → 提醒:间隔匹配变化速度,太闲的定时器是浪费。

### 第 4 步 · 契约草拟(仅当裁决为 loop)

**goal loop** → 按四零件草拟,规则:
- **目标**:可判定,数字或布尔;
- **校验**:必须绑定第 1 步找到的**真实命令**(如 `pnpm test`、现成 bench 脚本),禁止「请在此填入你的测试」式占位符;要求每轮贴出命令输出作证据;
- **边界/规矩**:堵近路——问一遍「目标定成这样,最省事的作弊是什么?」,逐条封死(改裁判/偷工/减料/空口汇报四个方向自查);
- **停止**:达标即收 + N 轮兜底(`or stop after N turns`)。

**定时器 loop** → 给出 /loop 提示词骨架(目标=每轮要**维持的状态**;校验含 no-op 诚实条款——无事可做如实报告,不许制造改动;边界=操作白名单+负面清单;停止=由人取消+连续 no-op 自我建议停),然后**移交下游,不重造**:
- 模式选择与生产加固 → [cobusgreyling/loop-engineering](https://github.com/cobusgreyling/loop-engineering)(pattern-picker、loop-design-checklist、loop-audit);
- GitHub backlog 场景 → 直接用本仓库的 `backlog-manager` skill;
- 成例参考 → [crazynomad/tutorial 的 14-loop](https://github.com/crazynomad/tutorial/tree/main/14-loop)(四个真实 demo,含 manager/developer 双循环提示词全文)。

## 不做的事

- 不做 loop 模式库、成本估算、审计打分——cobusgreyling/loop-engineering 已有,推荐即可。
- 不替用户写「什么算做完」的实质内容——那是出题人的活,skill 只把问题逼到面前。
- 证据不足时不硬给裁决——写明缺什么(如「没有任何可跑的测试」),给出补齐路线。
