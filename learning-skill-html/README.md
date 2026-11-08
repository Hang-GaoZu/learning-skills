# learning-skill-html

触发范围：**仅在用户明确要求 HTML 版课程、学习站点或网页，或直接指名 `$learning-skill-html` 时启用**；若只是推进课程内容而未提 HTML，改用 `learning-skill`。

把结构化课程生成成可直接双击使用的离线 HTML 学习站点。它保留原 `learning-skill` 的教学闭环，同时为主笔记、自测、步骤、卡片、课程状态和 N+2 草稿提供各自独立的页面与入口。

## 主要能力

- **一课一页**：主页只做导航，不把所有正文堆进同一个超长页面。
- **课程主线**：用从左到右的总线展示步骤、分支、掌握状态和复习标记。
- **自动概况**：课程推进、验收掌握度和待复习数量由 `course-state.json` 计算。
- **动态演示**：内置流程、代码追踪、图形与代码双栏、提交后反馈四类组件。
- **离线优先**：CSS、JavaScript 和课程资源全部随站点携带，不依赖 CDN 或本地服务器。
- **跨会话续学**：状态、最近验收、薄弱点和复习队列集中在机器可读的 JSON 中。
- **教学约束**：仍要求七要素、源卡片与打字卡片（打字页是空白默写）、出口验收、错题回收和 N+2 备课。

## 目录结构

```text
learning-skill-html/
├── SKILL.md
├── README.md
├── agents/
│   └── openai.yaml
├── assets/
│   └── site-template/
│       ├── app.js
│       ├── document-template.html
│       ├── index-template.html
│       └── style.css
├── examples/
│   └── quickstart/
├── references/
│   ├── course-state-migration.md
│   ├── html-course-spec.md
│   └── teaching-rules.md
└── scripts/
    ├── build_course_site.py
    └── validate_site.py
```

## 快速开始

1. 准备一个课程源目录，至少包含：

```text
course-site-source/
├── course.json
├── course-state.json
└── content/
    ├── notes.html
    ├── self-test.html
    ├── step-01.html
    ├── cards-source.html
    ├── cards-typing.html
    ├── learning-overview.html
    ├── course-state.html
    └── next-outline.html
```

2. 参照 `examples/quickstart` 编辑清单、状态和正文。`course.json` 决定入口与页面，`course-state.json` 决定进度。
3. 生成站点：

```powershell
$env:PYTHONUTF8 = "1"
python <skill-dir>/scripts/build_course_site.py --manifest .\course.json --output .\site
python <skill-dir>/scripts/validate_site.py .\site
```

4. 双击 `site/index.html` 检查导航、动态演示和窄屏布局。

重新生成已由本技能创建的站点时，可以加 `--allow-existing`：

```powershell
python <skill-dir>/scripts/build_course_site.py --manifest .\course.json --output .\site --allow-existing
```

生成器只删除自己记录过的旧页面；非空且没有 `.learning-skill-html.json` 标记的目录不会被直接覆盖。

## 文档类型

| `kind` | 用途 | 建议入口 |
|---|---|---|
| `notes` | 主笔记与累计比喻地图 | 进入主笔记 |
| `step` | 单个教学步骤 | 学习第 N 步 |
| `quiz` | 自测与出口验收 | 开始自测 |
| `cards-source` | 源记忆卡片 | 查看源卡片 |
| `cards-typing` | 打字空白默写 | 打开打字默写 |
| `progress` | 自动计算的课程主线 | 打开课程主线 |
| `state` | 详细状态与复习记录 | 查看进度与复习 |
| `draft` | N+2 备课草稿 | 查看下一阶段草稿 |
| `support` | 术语表、实验记录等 | 由文档标题决定 |

`progress` 必须且只能有一份。不要再创建相互竞争的“学习路线”和“学习概况”两个页面。

## 状态文件

最小结构见 `references/html-course-spec.md#机器状态`。核心规则：

- `steps` 必须是非空数组；
- 状态只允许 `mastered`、`half`、`failed`、`skipped`、`unlearned`；
- `file` 必须指向 `course.json` 中真实存在的页面，尚未建立的步骤留空；
- 课程推进按“非未学习步骤数 / 总步骤数”计算；
- 掌握度按 `mastered = 1`、`half = 0.5`、其余为 `0` 加权；
- 待复习数量来自 `review_queue` 中尚未完成或清除的条目。

旧课程迁移请阅读 `references/course-state-migration.md`。

## 动态组件

教学正文可直接使用以下标记：

- `data-demo="flow"`：流程节点前进、后退、自动播放与重置；
- `data-demo="trace"`：代码行、变量和说明同步；
- `data-demo="duet"`：图形场景与代码行同步；
- `data-quiz`：提交后才显示反馈。

组件的完整示例和可访问性要求见 `references/html-course-spec.md`。所有交互必须支持键盘、窄屏和 `prefers-reduced-motion`。

## 示例与校验

示例课程位于：

```text
examples/quickstart/course.json
examples/quickstart/course-state.json
examples/quickstart/site/index.html
```

结构校验：

```powershell
$env:PYTHONUTF8 = "1"
python <skill-creator-dir>/scripts/quick_validate.py <skill-dir>
python <skill-dir>/scripts/validate_site.py .\site
```

站点校验会检查：

- 首页是否覆盖每份文档；
- 相对链接和锚点是否有效；
- 是否混入远程资源；
- 课程主线、首页概况和动态组件是否存在；
- 首页与完整概况页的进度数字是否一致。

浏览器交付前还应手动检查：动态演示可按预期变化、提交前答案不可见、桌面与 320px 窄屏无横向溢出、键盘焦点清楚。

## 运行要求

- Python 3.10 或更高版本；
- 不需要第三方 Python 包，不需要 Node.js，不需要网络；
- Windows 中文环境下建议设置 `PYTHONUTF8=1`，避免读取 UTF-8 Markdown 时受系统代码页影响。

## 相关文档

- `SKILL.md`：Codex 执行入口与不可省略的教学闭环；
- `references/teaching-rules.md`：摸底、讲解、验收、复习规则；
- `references/html-course-spec.md`：站点、状态和组件的完整规范；
- `references/course-state-migration.md`：旧课程迁移方法。
