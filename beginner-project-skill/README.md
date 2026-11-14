# Beginner Project Skill · 新手项目学习

> A skill for AI coding agents that walks a total beginner through building their **first runnable project** — and leaves behind teaching documents they can keep learning from.
>
> 一个给 AI 编程助手用的技能：带零基础的人真正做出**第一个能跑的项目**，并留下可以反复回看的教学文档。

**关键词 / Keywords**：AI skill · agent skill · SKILL.md · Claude Code · Codex · learn by building · project-based learning · beginner-friendly · first mini game · starter project · tutorial · teaching docs · 项目型陪练 · 记忆卡片

---

## English Overview

- **What it is** — a `SKILL.md` skill for AI coding agents that takes a total beginner from zero to a **first runnable project**, and leaves durable Markdown teaching docs behind.
- **How it works** — Step 0 environment self-check → 3–6 runnable milestones → per milestone: predict → run → compare → locate → fix → variant transfer → exit check → checkpoint.
- **Three layers** — state / logic / render kept apart, with input treated as a separate boundary, so problems get localized to "which layer".
- **Two optional modules** — Git backup (falls back to folder snapshots when the learner doesn't know Git) and learner-authored comments; decided by a quick pre-assessment and switchable mid-course.
- **Deliverables** — `项目笔记.md` (project notes), `第N步-主题.md` (per-milestone teaching pages), card source/typing pair, and `project-state.md` for resuming across sessions.
- **Install** — drop the folder into your agent's skills directory (`~/.claude/skills/`, `~/.codex/skills/`, or whatever root your tool scans). Pure Markdown, no runtime dependencies.

## 它解决什么问题

新手做第一个项目，通常败在两处：一是环境没跑通就开写业务逻辑，二是被人甩了一整段代码却什么都没学会。这个技能把两件事都管住：

- **先环境，后逻辑**：第 0 步只做一件事——让最小程序在学员自己的机器上跑出可见输出，并把构建命令逐词讲清。不通过不往下走。
- **小里程碑 + 运行反馈循环**：每个里程碑都能独立运行、都有肉眼可见的结果，走一遍「先预测 → 再运行 → 对比观察 → 定位修正」。
- **不代写，只陪练**：主体逻辑由学员自己写；AI 负责讲构件、出预测题、审查代码、定位错误层级。环境搭建、脚手架、读报错可以代劳——那不是学习目标。
- **难度可调，不搞一刀切**：Git 备份与「学员自己写注释」是**可选模块**，开讲前问一句，按学员底子与意愿开关；不会 Git 就改用文件夹快照备份，照样有后悔药。

## 核心机制

| 机制 | 作用 |
|---|---|
| 环境自检（第 0 步） | 先把"能跑"这件事落实，避免后面全盘塌方 |
| 里程碑拆分 | 把"做个游戏"砍成 3–6 个可运行的小步，每步都有可见结果 |
| 预测—运行—对比 | 动工前先问"你预期看到什么"，逼出真实理解程度，再揭晓 |
| 三层结构 | 状态层 / 逻辑层 / 渲染层分离，输入层另算——定位错误时用"哪一层"说话 |
| 代码出场顺序 | 新面孔清单 → 逐个讲透 → 学员动手 → 验收后才给完整代码 |
| 备份不裸奔 | 会 Git 就教检查点与四种「追回」场景；不会 Git 就用文件夹快照，保证任何一步都能退回 |
| 注释双轨 | 导师注必做（讲清"为什么这么注"）；学员注可选，开启则走「评注 → 仿写 → 互评 → 验收」四步 |
| 教学文档五件套 | `项目笔记.md`、`第N步-主题.md`、卡片源 / 打字两件套、`project-state.md` |
| N+2 预备 | 学到第 N 步时先备好第 N+2 步的大纲与卡片草稿，保持节奏不掉线 |

## 两个可选模块

开讲前先摸底，再决定开或关；结论写进 `project-state.md`，续学时不必重新猜。

| 模块 | 摸底问话 | 处理 |
|---|---|---|
| **Git 备份** | "用过 git 吗？会 commit / 回到上一版吗？" | 没用过 → 不必硬教，改用**文件夹快照备份**（每个验收节点复制一份源码）；会一点 → 只教 `status`/`add`/`commit`/`restore` 最小集；熟练 → 按全套来，检查点、提交信息、diff 复盘、追回场景一个都不含糊 |
| **学员自写注释** | "想自己动手写注释，还是只听我讲？" | 想写 → 开启，走「评注 → 仿写 → 互评 → 验收」；不想写 → 关闭，导师照旧写正式注释并逐条讲清用意，但不布置作业、不纳入验收 |

两项**都不默认开启**，学员说"随便"时才按底子处理；中途改主意随时可开可关，不追溯旧步骤。原则一句话：**可以少教，但备份不许缺、讲解不许省。**

## 目录结构

```
beginner-project-skill/
├── SKILL.md                      # 主入口：触发条件、核心流程、检查清单
├── agents/
│   └── openai.yaml               # 展示名与一句话简介
├── references/                   # 执行细则，按需读取
│   ├── milestones.md             # 里程碑拆分模板 + 贪吃蛇完整示例 + 规模降级
│   ├── loop.md                   # 迭代反馈循环节拍、预测题模板、四象限定位表
│   ├── code-explanation.md       # 代码出场顺序、函数四要素、变量四件套、三档注释、学员自写注释四步法
│   ├── git-and-debug.md          # Git 摸底三档、检查点节奏、四种追回、无 Git 时的快照备份、调试三板斧
│   ├── teaching-doc.md           # 五件产物模板、单步教学页、卡片源/打字规范
│   └── project-state.md          # 状态文件模板、跨会话恢复、旧状态冲突处理
└── examples/
    └── quickstart/               # 一套已生成的真实产物样例（贪吃蛇·C 终端版）
```

## 安装

本技能是纯 Markdown（`SKILL.md` + 引用文档），不依赖任何脚本或运行时，因此**与具体 agent 无关**：

1. 把整个目录放进你所使用 agent 的 skills 目录，例如：
   - Claude Code：`~/.claude/skills/beginner-project-skill/`
   - Codex：`~/.codex/skills/beginner-project-skill/`
   - 其他支持 `SKILL.md` 约定的工具：放入其约定的 skills 根目录
2. 重新加载 / 重启该 agent，使其扫描到新的 skill。
3. 触发方式：让助手"按步骤带我做第一个小游戏 / 小工具"，或说 "learn by building"、"starter project"。

> 本技能只负责「从零做一个项目」。若你另有一套知识点系统课程技能（例如 `learning-skill`），二者可以分工：本技能管项目推进，课程技能管知识补课，卡点补 3 次仍不通时回流到课程技能。

## 怎么读这份仓库

- 想快速理解它怎么运作 → 先读 `SKILL.md`，那是主入口。
- 想知道具体怎么写每一步 → 读 `references/loop.md` 与 `references/teaching-doc.md`。
- 想看产物长什么样 → 打开 `examples/quickstart/`，从 `README.md` 开始。
- 想改它的教学风格 → 主要改 `references/code-explanation.md` 与 `SKILL.md` 的「反馈原则」一节。

## 边界（什么情况下不该用它）

- 用户只要一个能跑的成品、明确说"直接给我代码" → 不套本流程。
- 单次零散的 API / 概念答疑 → 直接回答即可。
- 纯知识点学习、且没有"做项目"意图 → 属于课程型技能的地盘。
- 用户说"只解释别改文件" → 只口头讲解，不创建任何文档。

## 贡献

欢迎提 Issue 与 PR。若要改动核心流程，建议一并更新 `SKILL.md` 与对应 `references/` 文档，避免规则自相矛盾；示例产物请保持与 `references/teaching-doc.md` 的模板一致。

## License

[MIT](LICENSE) © 2026 Hang-GaoZu
