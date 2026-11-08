# Codex Learning Skills

A pair of complementary **Codex skills** for structured one-on-one tutoring, designed around an active-learning loop. These skills help you build and run a guided course that keeps the learner engaged: predict first, trace the state, get immediate feedback, then transfer the idea to a new variant.

This repository contains two skills:

| Skill | Format | Description |
|---|---|---|
| `learning-skill` | Markdown | Progress a structured course step-by-step in Markdown, maintaining notes, self-tests, source/typing cards, a learning dashboard, and `course-state.md`. |
| `learning-skill-html` | Offline HTML | Same teaching loop, but generates a self-contained offline HTML learning site with a progress timeline, per-page navigation, and dynamic demos. |

Both skills share the same pedagogy and are meant to work together: use `learning-skill` for day-to-day course progression in Markdown, and `learning-skill-html` when you (or the learner) want a browsable, offline HTML site.

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

---

## Repository layout

```
learning-skills/
├── README.md                # This file (English + Chinese summary)
├── LICENSE                  # MIT
├── learning-skill/          # Markdown-based tutoring skill
│   ├── SKILL.md             # Codex skill entrypoint
│   ├── README.md            # Skill-specific README (Chinese)
│   ├── references/          # teaching-rules, cards, course-files, delivery-checklist
│   ├── examples/quickstart/ # A minimal sample course
│   └── scripts/
└── learning-skill-html/     # Offline HTML learning site generator
    ├── SKILL.md             # Codex skill entrypoint
    ├── README.md            # Skill-specific README (Chinese)
    ├── agents/openai.yaml
    ├── assets/site-template/  # CSS/JS/HTML templates for the generated site
    ├── references/            # html-course-spec, teaching-rules, course-state-migration
    ├── examples/quickstart/   # Sample course source + generated site
    └── scripts/
        ├── build_course_site.py  # Build the offline HTML site
        └── validate_site.py      # Validate the generated site
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

---

## Validation

Both skills include validation scripts (no dependencies required):

```powershell
$env:PYTHONUTF8 = "1"
python <skill-creator>/scripts/quick_validate.py <skill-dir>       # structure check
python <learning-skill-html>/scripts/validate_site.py .\site        # generated site check
```

---

## Requirements

- **Codex** (or any agent that loads `SKILL.md` skills) for the Markdown skill.
- **Python 3.10+** for the HTML site generator.
- Set `PYTHONUTF8=1` on Windows to avoid UTF-8 reading issues.

---

## License

[MIT](LICENSE)

---

## 中文简介 (Chinese Summary)

`learning-skill` 与 `learning-skill-html` 是一对互补的 Codex 技能，用于**一对一定向结构化教学**。两者都围绕「先预测 → 双轨走查 → 即时反馈 → 变式迁移」的主动学习循环组织每一步，并维护跨步累进比喻地图、学习看板、源/打字卡片、出口验收与错题回收。

- **learning-skill（Markdown 版）**：按既定课程连续推进，同步主笔记、自测题、各步教学文档与 `course-state.md`。适合在 Typora 等 Markdown 阅读器中阅读。
- **learning-skill-html（离线 HTML 版）**：同一教学闭环，额外生成可直接双击使用的离线 HTML 学习站点——首页导航、课程主线总线、每步独立页面与图形/代码同步动态演示。

使用方式：日常推进课程用 `learning-skill`；需要网页版课程或学习站点时用 `learning-skill-html`。

更多细节见各技能目录下的 `README.md`（中文）与 `SKILL.md`。
