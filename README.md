# AI Learning Skills

Three complementary **agent skills** (Codex / Claude Code / any agent that loads `SKILL.md`) for structured one-on-one tutoring and learn-by-building projects. Every skill is built around the same conviction: a learner remembers what they predicted, traced, and fixed — not what they were told.

This repository contains three skills:

| Skill | Format | Description |
|---|---|---|
| `learning-skill` | Markdown | Progress a structured course step by step in Markdown: main notes, self-tests, source/typing cards, a learning dashboard, and `course-state.md`. |
| `learning-skill-html` | Offline HTML | Same teaching loop, but generates a self-contained offline HTML learning site with a progress timeline, per-page navigation, and dynamic demos. |
| `beginner-project-skill` | Markdown | Take a beginner from zero to a first *runnable* project (mini game, small tool, starter app): environment self-check → small milestones → predict-run-compare loop, leaving keepable Markdown teaching docs. |

The first two share one pedagogy and are meant to work together: `learning-skill` for day-to-day course progression in Markdown, `learning-skill-html` when you (or the learner) want a browsable offline site. The third is the "first project" on-ramp — it assumes no prior knowledge and optimizes for a running artifact quickly.

---

## Why these skills?

### Active learning loop
Every step is organized around a **predict → trace → feedback → transfer** cycle:

1. **Predict first** — before revealing a concept, ask the learner to guess the next state, result, or line.
2. **Dual-track tracing** — align a "metaphor-world state" with the code/flow and the variable/output, advancing one observable state at a time.
3. **Immediate feedback** — judge the answer in one sentence; wrong answers go into a review queue.
4. **Variant transfer** — change one condition/parameter/scenario and ask whether the model still holds or what the code must change.

### Pedagogical safeguards
- **Seven-element teaching** and a cross-step progressive metaphor map.
- **Source & typing cards**: the source card holds the full code; the typing card is a blank-recall version (only numbers and empty code blocks — no hints, no answers).
- **Exit acceptance** (application problems + old-step review) and **mistake recycling**.
- **Dependency order** and annotated forward references.
- **N+2 outline & card drafts** prepared when learning step N.
- Clear boundaries for light Q&A, explain-only (no file changes), and skip-if-understood modes.

### Beginner on-ramp
`beginner-project-skill` adds: an environment self-check before anything else, milestones small enough to finish in one sitting, a predict-run-compare loop instead of copy-paste, and Git backup taught as the first safety net (code comments optional).

---

## Repository layout

```
ai-learning-skills/
├── README.md                  # This file (English + Chinese summary)
├── LICENSE                    # MIT
├── learning-skill/            # Markdown-based tutoring skill
│   ├── SKILL.md               # skill entrypoint
│   ├── README.md              # skill-specific README (Chinese)
│   ├── references/            # teaching-rules, cards, course-files, delivery-checklist
│   └── examples/quickstart/   # a minimal sample course
├── learning-skill-html/       # offline HTML learning site generator
│   ├── SKILL.md               # skill entrypoint
│   ├── README.md              # skill-specific README (Chinese)
│   ├── agents/openai.yaml
│   ├── assets/site-template/  # CSS/JS/HTML templates for the generated site
│   ├── references/            # html-course-spec, teaching-rules, course-state-migration
│   ├── examples/quickstart/   # sample course source + generated site
│   └── scripts/
│       ├── build_course_site.py   # build the offline HTML site
│       └── validate_site.py       # validate the generated site
└── beginner-project-skill/    # zero-to-first-project skill
    ├── SKILL.md               # skill entrypoint
    ├── README.md              # skill-specific README (Chinese)
    ├── agents/openai.yaml
    ├── references/            # milestones, loop, code-explanation, git-and-debug, teaching-doc, project-state
    └── examples/quickstart/   # a sample first project (checkers board)
```

---

## Quick start

### learning-skill (Markdown)
1. Locate (or create) `course-state.md` in your course directory.
2. Follow the active-learning loop defined in `references/teaching-rules.md`.
3. For a new session, simply say:

```
使用 learning-skill，读取 <course-dir>/course-state.md，按老规矩继续。
```

See `examples/quickstart/` for a minimal sample.

### learning-skill-html (Offline HTML site)
Requires **Python 3.10+**, no third-party packages, no Node.js, no network.

```powershell
# From a course source directory containing course.json + course-state.json + content/
$env:PYTHONUTF8 = "1"
python <skill-dir>/scripts/build_course_site.py --manifest .\course.json --output .\site
python <skill-dir>/scripts/validate_site.py .\site
```

Then open `site/index.html` in a browser. The generated site is fully offline (no CDN).

### beginner-project-skill (First runnable project)
1. Let the skill run its **environment self-check** first (compiler/runtime/editor, one line each).
2. Then say what you want to build, in plain words:

```
使用 beginner-project-skill，我想做一个贪吃蛇，零基础。
```

The skill proposes milestones, teaches one milestone at a time, and after each run asks you to **predict → run → compare**. See `examples/quickstart/` for a sample project notebook.

---

## Validation

```powershell
$env:PYTHONUTF8 = "1"
python <learning-skill-html>/scripts/validate_site.py .\site   # generated site check
```

---

## Requirements

- **An agent that loads `SKILL.md` skills** (Codex, Claude Code, or similar).
- **Python 3.10+** for the HTML site generator only.
- Set `PYTHONUTF8=1` on Windows to avoid UTF-8 reading issues.

---

## License

[MIT](LICENSE)

---

## 中文简介

本仓库收纳三个自用的**一对一教学技能**，共同的主张是：学习者真正记住的，是自己预测过、走查过、修过的那一步，而不是被告知的那句话。

| 技能 | 做什么 |
|---|---|
| `learning-skill`（Markdown 版） | 按既定课程连续推进，同步主笔记、自测题、各步教学文档与 `course-state.md`，适合 Typora 阅读。 |
| `learning-skill-html`（离线 HTML 版） | 同一教学闭环，额外生成可直接双击打开的离线学习站点：首页导航、课程主线总线、每步独立页面与图形/代码同步演示。 |
| `beginner-project-skill`（零基础启动版） | 用「环境自检 + 小里程碑 + 预测-运行-对比」把新手带成第一个能跑的项目（小游戏、小工具、starter project），留下可续学的 Markdown 文档，Git 备份与注释可选。 |

使用方式：日常推进课程用 `learning-skill`；要网页版课程用 `learning-skill-html`；带着完全零基础的人做出第一个能跑的东西，用 `beginner-project-skill`。

三者都围绕「先预测 → 双轨走查 → 即时反馈 → 变式迁移」的主动学习循环，并维护跨步累进比喻地图、学习看板、源/打字卡片、出口验收与错题回收。更多细节见各技能目录下的 `README.md` 与 `SKILL.md`。
