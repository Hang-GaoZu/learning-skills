(() => {
  "use strict";

  const root = document.documentElement;
  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");

  function initTheme() {
    const saved = localStorage.getItem("learning-skill-theme");
    const preferred = window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
    const initial = saved === "dark" || saved === "light" ? saved : preferred;
    applyTheme(initial);

    document.querySelectorAll("[data-theme-toggle]").forEach((button) => {
      button.addEventListener("click", () => {
        const next = root.dataset.theme === "dark" ? "light" : "dark";
        localStorage.setItem("learning-skill-theme", next);
        applyTheme(next);
      });
    });
  }

  function applyTheme(theme) {
    root.dataset.theme = theme;
    document.querySelectorAll("[data-theme-label]").forEach((label) => {
      label.textContent = theme === "dark" ? "浅色" : "深色";
    });
  }

  function initMenu() {
    const sidebar = document.getElementById("course-sidebar");
    const toggle = document.querySelector("[data-menu-toggle]");
    if (!sidebar || !toggle) return;

    const close = () => {
      sidebar.classList.remove("is-open");
      toggle.setAttribute("aria-expanded", "false");
    };

    toggle.addEventListener("click", () => {
      const open = !sidebar.classList.contains("is-open");
      sidebar.classList.toggle("is-open", open);
      toggle.setAttribute("aria-expanded", String(open));
    });

    sidebar.querySelectorAll("a").forEach((link) => link.addEventListener("click", close));
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape") close();
    });
  }

  function initReadingProgress() {
    const bar = document.querySelector("[data-reading-progress]");
    if (!bar) return;
    const update = () => {
      const height = document.documentElement.scrollHeight - window.innerHeight;
      const ratio = height > 0 ? Math.min(1, Math.max(0, window.scrollY / height)) : 0;
      bar.style.transform = `scaleX(${ratio})`;
    };
    window.addEventListener("scroll", update, { passive: true });
    window.addEventListener("resize", update);
    update();
  }

  function initFlows() {
    document.querySelectorAll('[data-demo="flow"]').forEach((demo) => {
      const stages = [...demo.querySelectorAll("[data-flow-stage]")];
      if (!stages.length) return;
      const previous = demo.querySelector("[data-flow-prev]");
      const next = demo.querySelector("[data-flow-next]");
      const play = demo.querySelector("[data-flow-play]");
      const reset = demo.querySelector("[data-flow-reset]");
      const status = demo.querySelector("[data-flow-status]");
      let index = 0;
      let timer = 0;

      const update = (announce = true) => {
        stages.forEach((stage, stageIndex) => {
          stage.classList.toggle("is-active", stageIndex === index);
          stage.classList.toggle("is-complete", stageIndex < index);
          if (stageIndex === index) stage.setAttribute("aria-current", "step");
          else stage.removeAttribute("aria-current");
        });
        if (previous) previous.disabled = index === 0;
        if (next) next.disabled = index === stages.length - 1;
        if (status && announce) {
          const title = stages[index].querySelector("strong")?.textContent || `第 ${index + 1} 步`;
          status.textContent = `当前：${title}（${index + 1}/${stages.length}）`;
        }
      };

      const stopPlayback = () => {
        window.clearTimeout(timer);
        timer = 0;
        if (play) play.textContent = "自动播放";
      };

      previous?.addEventListener("click", () => {
        stopPlayback();
        index = Math.max(0, index - 1);
        update();
      });
      next?.addEventListener("click", () => {
        stopPlayback();
        index = Math.min(stages.length - 1, index + 1);
        update();
      });
      reset?.addEventListener("click", () => {
        stopPlayback();
        index = 0;
        update();
      });
      play?.addEventListener("click", () => {
        stopPlayback();
        index = 0;
        update();
        play.textContent = "播放中…";
        const delay = reducedMotion.matches ? 1500 : 900;
        const advance = () => {
          if (index >= stages.length - 1) {
            stopPlayback();
            return;
          }
          index += 1;
          update();
          timer = window.setTimeout(advance, delay);
        };
        timer = window.setTimeout(advance, delay);
      });

      update(false);
    });
  }

  function initTraces() {
    document.querySelectorAll('[data-demo="trace"]').forEach((demo) => {
      const lines = [...demo.querySelectorAll("[data-trace-line]")];
      if (!lines.length) return;
      lines.forEach((line, index) => {
        line.dataset.lineNumber = String(index + 1);
      });
      const previous = demo.querySelector("[data-trace-prev]");
      const next = demo.querySelector("[data-trace-next]");
      const reset = demo.querySelector("[data-trace-reset]");
      const note = demo.querySelector("[data-trace-note]");
      const vars = demo.querySelector("[data-trace-vars]");
      let index = 0;

      const update = () => {
        lines.forEach((line, lineIndex) => {
          line.classList.toggle("is-active", lineIndex === index);
          if (lineIndex === index) line.setAttribute("aria-current", "step");
          else line.removeAttribute("aria-current");
        });
        if (previous) previous.disabled = index === 0;
        if (next) next.disabled = index === lines.length - 1;
        if (note) note.textContent = lines[index].dataset.traceNote || `执行第 ${index + 1} 行`;
        if (vars) {
          vars.replaceChildren();
          let values = {};
          try {
            values = JSON.parse(lines[index].dataset.traceVars || "{}");
          } catch {
            values = { 解析错误: "data-trace-vars 不是合法 JSON" };
          }
          Object.entries(values).forEach(([key, value]) => {
            const dt = document.createElement("dt");
            const dd = document.createElement("dd");
            dt.textContent = key;
            dd.textContent = String(value);
            vars.append(dt, dd);
          });
          if (!Object.keys(values).length) {
            const dt = document.createElement("dt");
            const dd = document.createElement("dd");
            dt.textContent = "状态";
            dd.textContent = "无局部变量";
            vars.append(dt, dd);
          }
        }
      };

      previous?.addEventListener("click", () => {
        index = Math.max(0, index - 1);
        update();
      });
      next?.addEventListener("click", () => {
        index = Math.min(lines.length - 1, index + 1);
        update();
      });
      reset?.addEventListener("click", () => {
        index = 0;
        update();
      });
      update();
    });
  }

  function initDuets() {
    document.querySelectorAll('[data-demo="duet"]').forEach((demo) => {
      const frames = [...demo.querySelectorAll("[data-duet-frame]")];
      const lines = [...demo.querySelectorAll("[data-duet-code]")];
      const states = [...demo.querySelectorAll("[data-duet-state]")];
      if (!frames.length && !lines.length && !states.length) return;
      const previous = demo.querySelector("[data-duet-prev]");
      const next = demo.querySelector("[data-duet-next]");
      const play = demo.querySelector("[data-duet-play]");
      const reset = demo.querySelector("[data-duet-reset]");
      const status = demo.querySelector("[data-duet-status]");
      const count = Math.max(frames.length, lines.length, states.length);
      let index = 0;
      let timer = 0;

      const update = (announce = true) => {
        frames.forEach((frame, frameIndex) => {
          frame.hidden = frameIndex !== index;
        });
        lines.forEach((line, lineIndex) => {
          line.classList.toggle("is-active", lineIndex === index);
        });
        states.forEach((state, stateIndex) => {
          state.hidden = stateIndex !== index;
        });
        if (previous) previous.disabled = index === 0;
        if (next) next.disabled = index === count - 1;
        if (status && announce) {
          const note = frames[index]?.dataset.duetNote || `第 ${index + 1} 步`;
          status.textContent = `${index + 1}/${count} · ${note}`;
        }
      };

      const stopPlayback = () => {
        window.clearTimeout(timer);
        timer = 0;
        if (play) play.textContent = "自动播放";
      };

      previous?.addEventListener("click", () => {
        stopPlayback();
        index = Math.max(0, index - 1);
        update();
      });
      next?.addEventListener("click", () => {
        stopPlayback();
        index = Math.min(count - 1, index + 1);
        update();
      });
      reset?.addEventListener("click", () => {
        stopPlayback();
        index = 0;
        update();
      });
      play?.addEventListener("click", () => {
        stopPlayback();
        index = 0;
        update();
        play.textContent = "播放中…";
        const delay = reducedMotion.matches ? 1500 : 1000;
        const advance = () => {
          if (index >= count - 1) {
            stopPlayback();
            return;
          }
          index += 1;
          update();
          timer = window.setTimeout(advance, delay);
        };
        timer = window.setTimeout(advance, delay);
      });

      update(false);
    });
  }

  function initQuizzes() {
    document.querySelectorAll("[data-quiz]").forEach((quiz) => {
      const reveal = quiz.querySelector("[data-quiz-reveal]");
      const reset = quiz.querySelector("[data-quiz-reset]");
      const feedback = quiz.querySelector("[data-quiz-feedback]");
      const input = quiz.querySelector("textarea, input");
      if (!reveal || !feedback) return;

      reveal.addEventListener("click", () => {
        feedback.hidden = false;
        reveal.setAttribute("aria-expanded", "true");
        reveal.textContent = "反馈已显示";
      });
      reset?.addEventListener("click", () => {
        feedback.hidden = true;
        reveal.setAttribute("aria-expanded", "false");
        reveal.textContent = "提交并查看反馈";
        if (input) {
          input.value = "";
          input.focus();
        }
      });
    });
  }

  function initTyping() {
    document.querySelectorAll("[data-typing]").forEach((panel) => {
      const field = panel.querySelector("[data-typing-field]");
      const clear = panel.querySelector("[data-typing-clear]");
      const status = panel.querySelector("[data-typing-status]");
      if (!field) return;

      const update = () => {
        if (!status) return;
        const length = field.value.trim().length;
        status.textContent = length ? `已输入 ${length} 个字符；写完再对照源卡片。` : "尚未开始。";
      };

      field.addEventListener("input", update);
      clear?.addEventListener("click", () => {
        field.value = "";
        update();
        field.focus();
      });
      update();
    });
  }
  initTheme();
  initMenu();
  initReadingProgress();
  initFlows();
  initTraces();
  initDuets();
  initQuizzes();
  initTyping();
})();
