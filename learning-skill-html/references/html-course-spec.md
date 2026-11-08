# 离线 HTML 课程规范

## 总原则

站点必须可直接双击 `index.html` 使用，不依赖本地服务器或网络。所有 CSS、JavaScript、字体回退和图片均随站点携带。学习者可见文档 HTML 优先；Markdown 或 JSON 只作为便于维护的源材料。

首页是唯一启动入口，但不是唯一页面。每一份文档有独立 HTML 和独立入口按钮。所有页面共享清晰的返回总览和前后文档导航。

为避免入口过多，首页采用渐进式呈现：课程主线、主笔记、当前步骤、自测和记忆训练直接显示；课程状态、N+2 草稿、章节脉络、术语表和实验记录等低频资料放入可折叠分组。折叠只影响首页展示，不合并页面，也不取消独立按钮。

## 必备页面

以下页面在课程开始时建立，之后持续更新：

| `kind` | 页面 | 入口 |
|---|---|---|
| `notes` | 主笔记 | 进入主笔记 |
| `step` | 各步教学 | 学习第 N 步 |
| `quiz` | 自测题 | 开始自测 |
| `cards-source` | 源卡片 | 查看源卡片 |
| `cards-typing` | 打字卡片 | 打开打字练习 |
| `progress` | 课程主线 | 打开课程主线 |
| `state` | 课程状态 | 查看进度与复习 |
| `draft` | N+2 草稿 | 查看下一阶段草稿 |

章节脉络、术语表、实验记录等独立文档使用 `kind: "support"`，不能只塞进主笔记。

## 机器状态

`course.json` 的 `course.state_file` 必须指向状态文件。`course-state.json` 保存跨会话恢复所需的最小结构：

```json
{
  "schema_version": 1,
  "course": {
    "title": "课程名",
    "current_step": 3,
    "completed_steps": [1, 2],
    "prepared_step": 5,
    "last_updated": "2026-11-01"
  },
  "steps": [
    {
      "number": 1,
      "title": "三关口模型",
      "chapter": "基础流程",
      "status": "mastered",
      "file": "step-01.html",
      "branches": [
        {
          "title": "三个关口各管一件事",
          "status": "mastered",
          "file": "step-01.html"
        },
        {
          "title": "出口验收",
          "status": "mastered",
          "file": "self-test.html"
        }
      ]
    },
    {
      "number": 2,
      "title": "队列背压",
      "chapter": "基础流程",
      "status": "unlearned",
      "branches": [
        { "title": "容量边界", "status": "unlearned" },
        { "title": "拒绝策略", "status": "unlearned" }
      ]
    }
  ],
  "documents": {
    "notes": "notes.html",
    "current_lesson": "step-03.html",
    "quiz": "self-test.html",
    "cards_source": "cards-source.html",
    "cards_typing": "cards-typing.html",
    "learning_overview": "learning-overview.html",
    "state": "course-state.html",
    "next_outline": "next-outline.html"
  },
  "acceptance": [],
  "review_queue": [],
  "weak_points": []
}
```

`status` 只允许 `mastered`、`half`、`failed`、`skipped`、`unlearned`。`file` 可以是已生成的教学步骤页面；尚未生成的步骤留空。

状态用于决定继续哪一步、哪些草稿仍有效以及下次复习什么。生成器据此计算：

- 课程推进 = 状态不是 `unlearned` 的步骤数 / 总步骤数；
- 验收掌握度 = 权重总和 / 总步骤数，其中 `mastered=1`、`half=0.5`，其余为 0；
- 待复习 = `review_queue` 中状态不是 `done` 或 `cleared` 的条目数；
- 下一步建议和下一里程碑。

HTML 课程状态页用于详细记录，课程主线页用于面向学习者的摘要、可视路线和进度。

## 页面内容

### 首页

- 课程标题、用途和当前状态；
- 按“开始学习 / 核心文档 / 练习与记忆 / 进度管理”等类别分组；
- 每个文档一张入口卡，显示标题、一句说明、状态标签和专用按钮；
- 高频入口直接显示，低频分组默认折叠；
- 不堆叠全部正文。

### 文档页

- 顶部显示课程、文档类别、标题和最后更新时间；
- 桌面左侧显示完整文档索引，当前页高亮；
- 正文和自动生成的上一份/下一份导航；
- 长文提供阅读进度；
- 返回 `index.html` 的路径始终有效。

### 课程主线页

- 顶部显示验收掌握度、课程推进、已掌握步骤和待复习数量；
- 给出一个明确的下一步建议；
- 用一条从左到右的总线连接所有主节点，每步显示状态和复习标记；
- 展开节点后展示该节点的分支内容、状态和可进入页面；
- 展示复习队列、当前薄弱点和最近五次验收；
- 数据必须由 `course-state.json` 生成，不手写百分比。

### 首页学习概况

- 放在当前任务卡片之后，不替代“继续学习”主按钮；
- 展示课程推进、验收掌握度、当前步骤、待复习和下一里程碑；
- 提供“查看完整概况”入口；
- 不显示虚假的积分、连续签到或预计完成日期。

### 图形与代码同步演示

需要理解执行过程或数据流动时，优先使用 `data-demo="duet"` 双栏组件。左栏显示图形类比，右栏显示代码，第三区显示当前说明。作者需要让以下三项一一对应：

- 每张 `[data-duet-frame]` 图；
- 每行 `[data-duet-code]` 代码；
- 每段 `[data-duet-state]` 说明。

步进时三者同时切换，不能用与代码无关的装饰动画替代。图形应沿用课程的累计比喻地图，并支持上一步、下一步、自动播放和重置。

### 教学步骤页

必须包含七要素。动态演示放在概念解释与练习之间，不能替代练习和验收。

## 动态组件

### 流程演示

```html
<section class="demo" data-demo="flow" aria-labelledby="flow-title">
  <div class="demo-head">
    <div>
      <p class="kicker">动态流程</p>
      <h2 id="flow-title">一次请求如何经过三个关口</h2>
    </div>
    <div class="demo-actions">
      <button type="button" data-flow-prev>上一步</button>
      <button type="button" class="primary" data-flow-next>下一步</button>
      <button type="button" data-flow-play>自动播放</button>
      <button type="button" data-flow-reset>重置</button>
    </div>
  </div>
  <ol class="flow-rail">
    <li data-flow-stage>
      <span class="node">1</span>
      <strong>排队</strong>
      <small>请求进入队列</small>
    </li>
    <li data-flow-stage>
      <span class="node">2</span>
      <strong>处理</strong>
      <small>工作单元读取数据</small>
    </li>
    <li data-flow-stage>
      <span class="node">3</span>
      <strong>返回</strong>
      <small>结果回写调用方</small>
    </li>
  </ol>
  <p class="demo-status" data-flow-status aria-live="polite"></p>
</section>
```

### 代码追踪

```html
<section class="demo" data-demo="trace" aria-labelledby="trace-title">
  <div class="demo-head">
    <div>
      <p class="kicker">代码追踪</p>
      <h2 id="trace-title">每一步变量发生了什么</h2>
    </div>
    <div class="demo-actions">
      <button type="button" data-trace-prev>上一步</button>
      <button type="button" class="primary" data-trace-next>下一步</button>
      <button type="button" data-trace-reset>重置</button>
    </div>
  </div>
  <div class="trace-layout">
    <pre class="trace-code"><code><span data-trace-line data-trace-note="创建计数器" data-trace-vars='{"count":"0"}'>int count = 0;</span>
<span data-trace-line data-trace-note="第一次累加" data-trace-vars='{"count":"1"}'>count += 1;</span>
<span data-trace-line data-trace-note="第二次累加" data-trace-vars='{"count":"2"}'>count += 1;</span></code></pre>
    <div class="trace-state">
      <p class="kicker">当前状态</p>
      <p data-trace-note aria-live="polite"></p>
      <dl data-trace-vars></dl>
    </div>
  </div>
</section>
```

`data-trace-vars` 必须是合法 JSON 对象。生成内容要转义单引号，避免属性提前结束。

### 提交后反馈

```html
<section class="demo quiz" data-quiz aria-labelledby="quiz-title">
  <p class="kicker">小练习</p>
  <h2 id="quiz-title">如果把第三步删除，会发生什么？</h2>
  <textarea rows="4" aria-label="答案"></textarea>
  <div class="demo-actions">
    <button type="button" class="primary" data-quiz-reveal aria-expanded="false">
      提交并查看反馈
    </button>
    <button type="button" data-quiz-reset>重做</button>
  </div>
  <div class="quiz-feedback" data-quiz-feedback hidden>
    <strong>判定要点</strong>
    <p>调用方拿不到结果，后续依赖该结果的步骤不会开始。</p>
  </div>
</section>
```

答案在首次点击前必须保持 `hidden`。客观题可以有即时判定；开放题只给判定要点，最终掌握度仍由导师按出口验收记录。

## 自定义交互

内置组件不够时，可在单个正文片段增加隔离的 `<style>` 和 `<script>`。要求：

- 选择器只作用于该组件根节点；
- 不使用 `fetch`、XHR、WebSocket、动态 CDN 或内联远程资源；
- 避免 `innerHTML` 拼接用户输入；
- 给动态结果加 `aria-live="polite"`；
- 所有按钮使用原生 `<button type="button">` 并提供可见标签；
- 任何演示都提供重置方式。

## 内容与可访问性

- 页面语言设为 `zh-CN`，字体使用系统中文字体回退，不下载字体。
- 正文行宽适中，代码块允许横向滚动但页面本身不得横向溢出。
- 链接和按钮有清楚的键盘焦点；颜色不是唯一的状态表达。
- 动画支持 `prefers-reduced-motion`。
- 文字与背景对比充分；浅色和深色主题都可读。
- 打印时隐藏侧栏和按钮，保留正文与代码。

## 卡片页面约束

源卡片页可以包含：

- 卡片编号和概念名；
- 原始完整代码；
- 一句话记忆锚点；
- 源文件位置。

打字卡片页必须：

- 与源卡片同编号、同顺序；
- 是一张**空白默写页**：只给出编号和一个空白输入区，不提供代码骨架、缩进、变量名、占位符、要点或答案；
- 让用户先看源卡片，再凭记忆整段敲出代码，最后回到源卡片逐项对照；
- 判定按“结构、顺序、命名、边界”四项进行，而不是看占位符是否补齐；
- 不默认展开答案，也不在页面上提供可对照的正确答案。

## N+2 草稿约束

N+2 页面包含预期目标、前置依赖、大纲、候选比喻扩展和卡片草稿。若当前步未通过验收，在页面顶部显示“草稿已失效，下次基于当前掌握度重建”。

## 更新规则

- 新增文档：在 `course.json` 注册，在 `content/` 创建独立正文，重建站点；首页必须出现单独入口。
- 修改文档：只更新对应正文和状态，沿用现有 URL，避免无效旧入口。
- 删除文档：先从清单和内容移除，再运行生成器；只删除生成器记录的旧页面。
- 每步完成后重新校验所有相对链接和入口数量。
