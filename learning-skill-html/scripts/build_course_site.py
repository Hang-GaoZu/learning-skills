#!/usr/bin/env python3
"""Build an offline HTML course site from a manifest and HTML fragments."""

from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import sys
from datetime import date
from pathlib import Path
from typing import Any

MARKER_NAME = ".learning-skill-html.json"
SAFE_ID = re.compile(r"^[a-z0-9][a-z0-9-]*$")
STEP_STATUS_LABELS = {
    "mastered": "已掌握",
    "half": "半掌握",
    "failed": "未掌握",
    "skipped": "已跳过",
    "unlearned": "未学习",
}
STEP_STATUS_WEIGHTS = {
    "mastered": 1.0,
    "half": 0.5,
    "failed": 0.0,
    "skipped": 0.0,
    "unlearned": 0.0,
}


class BuildError(RuntimeError):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a navigable, offline HTML learning site."
    )
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument(
        "--allow-existing",
        action="store_true",
        help="Allow writing into a non-empty directory without a generation marker.",
    )
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise BuildError(f"清单不存在：{path}") from exc
    except json.JSONDecodeError as exc:
        raise BuildError(f"清单 JSON 无效：{path}:{exc.lineno}:{exc.colno}") from exc
    if not isinstance(value, dict):
        raise BuildError("清单根节点必须是 JSON 对象。")
    return value


def require_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise BuildError(f"{label} 必须是非空字符串。")
    return value.strip()


def safe_file_name(value: str, label: str) -> str:
    name = require_string(value, label)
    if Path(name).name != name or not name.endswith(".html"):
        raise BuildError(f"{label} 必须是当前目录下的 .html 文件名：{name}")
    if any(char in name for char in '<>:"/\\|?*'):
        raise BuildError(f"{label} 包含非法文件名字符：{name}")
    return name


def safe_source_path(base: Path, value: str, label: str) -> Path:
    raw = Path(require_string(value, label))
    if raw.is_absolute():
        raise BuildError(f"{label} 必须是相对于清单的路径。")
    resolved = (base / raw).resolve()
    try:
        resolved.relative_to(base.resolve())
    except ValueError as exc:
        raise BuildError(f"{label} 不能越过课程源目录：{raw}") from exc
    if not resolved.is_file():
        raise BuildError(f"{label} 指向的文件不存在：{resolved}")
    return resolved


def replace_tokens(template: str, tokens: dict[str, str]) -> str:
    output = template
    for key, value in tokens.items():
        output = output.replace("{{" + key + "}}", value)
    leftovers = sorted(set(re.findall(r"\{\{[A-Z0-9_]+\}\}", output)))
    if leftovers:
        raise BuildError(f"模板存在未替换占位符：{', '.join(leftovers)}")
    return output


def esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


def normalize_manifest(
    manifest: dict[str, Any], base: Path
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    course = manifest.get("course")
    if not isinstance(course, dict):
        raise BuildError("course 必须是 JSON 对象。")
    course_data = {
        "title": require_string(course.get("title"), "course.title"),
        "summary": require_string(course.get("summary"), "course.summary"),
        "status": str(course.get("status", "进行中")).strip() or "进行中",
        "current_step": str(course.get("current_step", "—")).strip() or "—",
        "updated": str(course.get("updated", date.today().isoformat())).strip(),
        "state_file": str(course.get("state_file", "")).strip(),
    }

    raw_groups = manifest.get("groups", [])
    if not isinstance(raw_groups, list):
        raise BuildError("groups 必须是数组。")
    groups: list[dict[str, Any]] = []
    group_ids: set[str] = set()
    for index, item in enumerate(raw_groups, 1):
        if not isinstance(item, dict):
            raise BuildError(f"groups[{index}] 必须是对象。")
        group_id = require_string(item.get("id"), f"groups[{index}].id")
        if not SAFE_ID.fullmatch(group_id):
            raise BuildError(f"分组 id 只能使用小写字母、数字和连字符：{group_id}")
        if group_id in group_ids:
            raise BuildError(f"分组 id 重复：{group_id}")
        group_ids.add(group_id)
        groups.append(
            {
                "id": group_id,
                "title": require_string(item.get("title"), f"groups[{index}].title"),
                "description": str(item.get("description", "")).strip(),
                "display": str(item.get("display", "primary")).strip(),
            }
        )
        if groups[-1]["display"] not in {"primary", "collapsed"}:
            raise BuildError(
                f"groups[{index}].display 只能是 primary 或 collapsed。"
            )

    raw_documents = manifest.get("documents")
    if not isinstance(raw_documents, list) or not raw_documents:
        raise BuildError("documents 必须是非空数组。")

    documents: list[dict[str, Any]] = []
    ids: set[str] = set()
    files: set[str] = set()
    for index, item in enumerate(raw_documents, 1):
        if not isinstance(item, dict):
            raise BuildError(f"documents[{index}] 必须是对象。")
        doc_id = require_string(item.get("id"), f"documents[{index}].id")
        if not SAFE_ID.fullmatch(doc_id):
            raise BuildError(f"文档 id 只能使用小写字母、数字和连字符：{doc_id}")
        if doc_id in ids:
            raise BuildError(f"文档 id 重复：{doc_id}")
        ids.add(doc_id)

        file_name = safe_file_name(item.get("file"), f"documents[{index}].file")
        if file_name == "index.html":
            raise BuildError("文档 file 不能是 index.html。")
        if file_name in files:
            raise BuildError(f"文档 file 重复：{file_name}")
        files.add(file_name)

        group_id = require_string(item.get("group"), f"documents[{index}].group")
        if group_id not in group_ids:
            raise BuildError(f"文档 {doc_id} 使用了未声明分组：{group_id}")

        source = safe_source_path(
            base, require_string(item.get("source"), f"documents[{index}].source"), "source"
        )
        body = source.read_text(encoding="utf-8")
        if "<!doctype" in body.lower() or "<html" in body.lower():
            raise BuildError(f"source 应为正文片段，不要包含 doctype/html：{source}")

        documents.append(
            {
                "id": doc_id,
                "title": require_string(item.get("title"), f"documents[{index}].title"),
                "description": require_string(
                    item.get("description"), f"documents[{index}].description"
                ),
                "entry_label": require_string(
                    item.get("entry_label", "进入文档"),
                    f"documents[{index}].entry_label",
                ),
                "file": file_name,
                "source": source,
                "body": body,
                "group": group_id,
                "kind": str(item.get("kind", "support")).strip() or "support",
                "badge": str(item.get("badge", "")).strip(),
                "icon": str(item.get("icon", "文")).strip()[:2] or "文",
                "order": index,
            }
        )

    used_groups = {doc["group"] for doc in documents}
    missing_groups = used_groups.difference(group_ids)
    if missing_groups:
        raise BuildError(f"存在未声明分组：{', '.join(sorted(missing_groups))}")
    extra_groups = group_ids.difference(used_groups)
    if extra_groups:
        raise BuildError(f"存在没有文档的分组：{', '.join(sorted(extra_groups))}")

    kinds = {doc["kind"] for doc in documents}
    for required_kind in ("notes", "state", "progress"):
        if required_kind not in kinds:
            raise BuildError(f"documents 至少需要一份 kind={required_kind} 的文档。")
    if sum(doc["kind"] == "progress" for doc in documents) != 1:
        raise BuildError("documents 必须且只能有一份 kind=progress 的文档。")
    if not course_data["state_file"]:
        raise BuildError("course.state_file 必须指向课程状态 JSON。")

    return course_data, groups, documents


def format_number(value: float) -> str:
    text = f"{value:.2f}".rstrip("0").rstrip(".")
    return text or "0"


def percent(value: float, total: float) -> float:
    return round(value / total * 100, 1) if total else 0.0


def load_progress(
    base: Path, course: dict[str, Any], documents: list[dict[str, Any]]
) -> dict[str, Any]:
    state_path = safe_source_path(base, course["state_file"], "course.state_file")
    state = read_json(state_path)
    state_course = state.get("course", {})
    if not isinstance(state_course, dict):
        raise BuildError("课程状态中的 course 必须是 JSON 对象。")

    raw_steps = state.get("steps")
    if not isinstance(raw_steps, list) or not raw_steps:
        raise BuildError("课程状态必须包含非空 steps 数组。")

    page_files = {doc["file"] for doc in documents}
    steps: list[dict[str, Any]] = []
    step_numbers: set[int] = set()
    for index, item in enumerate(raw_steps, 1):
        if not isinstance(item, dict):
            raise BuildError(f"steps[{index}] 必须是对象。")
        number = item.get("number")
        if not isinstance(number, int) or number < 1:
            raise BuildError(f"steps[{index}].number 必须是正整数。")
        if number in step_numbers:
            raise BuildError(f"步骤编号重复：{number}")
        step_numbers.add(number)

        status = str(item.get("status", "unlearned")).strip()
        if status not in STEP_STATUS_LABELS:
            raise BuildError(
                f"steps[{index}].status 无效：{status}；"
                f"允许值：{', '.join(STEP_STATUS_LABELS)}"
            )
        file_name = str(item.get("file", "")).strip()
        if file_name:
            file_name = safe_file_name(file_name, f"steps[{index}].file")
            if file_name not in page_files:
                raise BuildError(
                    f"steps[{index}].file 没有对应的文档页面：{file_name}"
                )
        raw_branches = item.get("branches", [])
        if not isinstance(raw_branches, list):
            raise BuildError(f"steps[{index}].branches 必须是数组。")
        branches: list[dict[str, Any]] = []
        for branch_index, branch in enumerate(raw_branches, 1):
            if not isinstance(branch, dict):
                raise BuildError(
                    f"steps[{index}].branches[{branch_index}] 必须是对象。"
                )
            branch_status = str(branch.get("status", "unlearned")).strip()
            if branch_status not in STEP_STATUS_LABELS:
                raise BuildError(
                    f"steps[{index}].branches[{branch_index}].status 无效。"
                )
            branch_file = str(branch.get("file", "")).strip()
            if branch_file:
                branch_file = safe_file_name(
                    branch_file, f"steps[{index}].branches[{branch_index}].file"
                )
                if branch_file not in page_files:
                    raise BuildError(
                        f"steps[{index}].branches[{branch_index}].file "
                        f"没有对应的文档页面：{branch_file}"
                    )
            branches.append(
                {
                    "title": require_string(
                        branch.get("title"),
                        f"steps[{index}].branches[{branch_index}].title",
                    ),
                    "status": branch_status,
                    "file": branch_file,
                }
            )
        steps.append(
            {
                "number": number,
                "title": require_string(item.get("title"), f"steps[{index}].title"),
                "chapter": str(item.get("chapter", "未分章")).strip() or "未分章",
                "status": status,
                "file": file_name,
                "branches": branches,
            }
        )
    steps.sort(key=lambda item: item["number"])

    state_current = str(
        state_course.get("current_step", course["current_step"])
    ).strip()
    current_number: int | None = None
    if state_current.isdigit():
        candidate = int(state_current)
        current_number = candidate if candidate in step_numbers else None
    current_step = next(
        (item for item in steps if item["number"] == current_number), None
    )

    total = len(steps)
    touched = sum(item["status"] != "unlearned" for item in steps)
    mastered_count = sum(item["status"] == "mastered" for item in steps)
    mastered_weight = sum(STEP_STATUS_WEIGHTS[item["status"]] for item in steps)
    status_counts = {
        status: sum(item["status"] == status for item in steps)
        for status in STEP_STATUS_LABELS
    }

    raw_reviews = state.get("review_queue", [])
    if not isinstance(raw_reviews, list):
        raise BuildError("课程状态中的 review_queue 必须是数组。")
    review_queue: list[dict[str, Any]] = []
    for index, item in enumerate(raw_reviews, 1):
        if not isinstance(item, dict):
            raise BuildError(f"review_queue[{index}] 必须是对象。")
        status = str(item.get("status", "due")).strip().lower()
        review_queue.append(
            {
                "concept": require_string(
                    item.get("concept"), f"review_queue[{index}].concept"
                ),
                "source_step": str(item.get("source_step", "—")).strip() or "—",
                "due": str(item.get("due", "—")).strip() or "—",
                "correct_streak": str(item.get("correct_streak", 0)).strip() or "0",
                "status": status,
            }
        )

    active_reviews = [
        item for item in review_queue if item["status"] not in {"done", "cleared"}
    ]
    review_step_numbers = {
        int(item["source_step"])
        for item in active_reviews
        if str(item["source_step"]).isdigit()
    }

    raw_acceptance = state.get("acceptance", [])
    if not isinstance(raw_acceptance, list):
        raise BuildError("课程状态中的 acceptance 必须是数组。")
    acceptance: list[dict[str, Any]] = []
    for index, item in enumerate(raw_acceptance, 1):
        if not isinstance(item, dict):
            raise BuildError(f"acceptance[{index}] 必须是对象。")
        acceptance.append(
            {
                "date": str(item.get("date", "—")).strip() or "—",
                "step": str(item.get("step", "—")).strip() or "—",
                "concept": str(item.get("concept", "—")).strip() or "—",
                "result": str(item.get("result", "—")).strip() or "—",
                "hint_level": str(item.get("hint_level", "—")).strip() or "—",
                "error_type": str(item.get("error_type", "—")).strip() or "—",
            }
        )

    next_unmastered = next(
        (item for item in steps if item["status"] != "mastered"), None
    )
    if active_reviews:
        next_action = f"先复习 {len(active_reviews)} 个待复习概念"
        next_action_reason = "因为当前主线仍有到期复习项"
    elif current_step and current_step["status"] in {"half", "failed"}:
        next_action = f"回练第 {current_step['number']} 步并完成变式题"
        next_action_reason = "因为当前节点还未通过出口验收"
    elif next_unmastered:
        next_action = f"开始第 {next_unmastered['number']} 步"
        next_action_reason = "按照依赖顺序进入下一个节点"
    else:
        next_action = "进行章末综合通关"
        next_action_reason = "全部节点已掌握，进入综合复习"

    if next_unmastered:
        next_milestone = (
            f"完成第 {next_unmastered['number']} 步"
            f"「{next_unmastered['title']}」并通过出口验收"
        )
    else:
        next_milestone = "全部步骤已掌握，进入章末综合复习"

    if mastered_weight == total:
        status_label = "课程已通关"
    elif active_reviews:
        status_label = "需要巩固"
    elif touched:
        status_label = "稳步推进"
    else:
        status_label = "尚未开始"

    chapter_map: dict[str, dict[str, Any]] = {}
    for step in steps:
        chapter = chapter_map.setdefault(
            step["chapter"],
            {
                "title": step["chapter"],
                "steps": [],
                "mastery_weight": 0.0,
                "touched": 0,
            },
        )
        chapter["steps"].append(step)
        chapter["mastery_weight"] += STEP_STATUS_WEIGHTS[step["status"]]
        chapter["touched"] += step["status"] != "unlearned"

    raw_weak_points = state.get("weak_points", [])
    if not isinstance(raw_weak_points, list):
        raise BuildError("课程状态中的 weak_points 必须是数组。")
    weak_points = [
        require_string(item, f"weak_points[{index}]")
        for index, item in enumerate(raw_weak_points, 1)
    ]

    return {
        "state_path": state_path,
        "steps": steps,
        "total": total,
        "touched": touched,
        "mastered_count": mastered_count,
        "mastered_weight": mastered_weight,
        "status_counts": status_counts,
        "review_queue": review_queue,
        "active_reviews": active_reviews,
        "review_step_numbers": review_step_numbers,
        "acceptance": acceptance,
        "weak_points": weak_points,
        "current_step_number": current_number or "—",
        "current_step_title": current_step["title"] if current_step else "—",
        "current_step_file": current_step["file"] if current_step else "",
        "next_step_number": next_unmastered["number"] if next_unmastered else "—",
        "next_milestone": next_milestone,
        "next_action": next_action,
        "next_action_reason": next_action_reason,
        "status_label": status_label,
        "chapters": list(chapter_map.values()),
        "prepared_step": str(state_course.get("prepared_step", "—")).strip() or "—",
        "last_updated": str(
            state_course.get("last_updated", course["updated"])
        ).strip()
        or course["updated"],
    }


def progress_bars_html(progress: dict[str, Any]) -> str:
    advance = percent(progress["touched"], progress["total"])
    mastery = percent(progress["mastered_weight"], progress["total"])
    return (
        '<div class="progress-bars">'
        '<div class="progress-bar-row">'
        '<div class="progress-bar-copy"><span>课程推进</span>'
        f'<strong>{esc(format_number(percent(progress["touched"], progress["total"])))}%</strong></div>'
        '<div class="progress-track" role="progressbar" aria-label="课程推进" '
        f'aria-valuemin="0" aria-valuemax="100" aria-valuenow="{format_number(advance)}">'
        f'<span style="width:{format_number(advance)}%"></span></div></div>'
        '<div class="progress-bar-row">'
        '<div class="progress-bar-copy"><span>验收掌握度</span>'
        f'<strong>{esc(format_number(percent(progress["mastered_weight"], progress["total"])))}%</strong></div>'
        '<div class="progress-track is-mastery" role="progressbar" aria-label="验收掌握度" '
        f'aria-valuemin="0" aria-valuemax="100" aria-valuenow="{format_number(mastery)}">'
        f'<span style="width:{format_number(mastery)}%"></span></div></div>'
        "</div>"
    )


def progress_snapshot_html(progress: dict[str, Any], progress_file: str) -> str:
    advance = format_number(percent(progress["touched"], progress["total"]))
    mastery = format_number(percent(progress["mastered_weight"], progress["total"]))
    return (
        '<section class="progress-snapshot" aria-labelledby="progress-snapshot-title" '
        f'data-progress-advance="{advance}" data-progress-mastery="{mastery}">'
        '<div class="progress-snapshot-copy">'
        '<p class="eyebrow">学习概况</p>'
        f'<h2 id="progress-snapshot-title">{esc(progress["status_label"])}</h2>'
        f'<p>{esc(progress["next_milestone"])}</p>'
        f"{progress_bars_html(progress)}"
        "</div>"
        '<div class="progress-snapshot-data">'
        '<div><span>当前步骤</span>'
        f'<strong>第 {esc(progress["current_step_number"])} 步</strong>'
        f'<small>{esc(progress["current_step_title"])}</small></div>'
        '<div><span>已掌握</span>'
        f'<strong>{esc(progress["mastered_count"])} / {esc(progress["total"])}</strong>'
        f'<small>加权掌握 {esc(format_number(progress["mastered_weight"]))} 步</small></div>'
        '<div><span>待复习</span>'
        f'<strong>{esc(len(progress["active_reviews"]))} 项</strong>'
        f'<small>{esc(progress["next_action"])}</small></div>'
        f'<a class="entry-button" href="{esc(progress_file)}">'
        '查看完整概况<span aria-hidden="true">→</span></a>'
        "</div></section>"
    )


def status_badge_html(status: str) -> str:
    return (
        f'<span class="status-pill status-{esc(status)}">'
        f'{esc(STEP_STATUS_LABELS[status])}</span>'
    )


def course_bus_html(progress: dict[str, Any]) -> str:
    chunks = [
        '<div class="course-bus" data-course-bus '
        f'data-node-count="{len(progress["steps"])}">'
        '<div class="bus-line">'
    ]
    for step in progress["steps"]:
        is_current = step["number"] == progress["current_step_number"]
        open_attr = " open" if is_current else ""
        current_attr = ' aria-current="step"' if is_current else ""
        review_flag = (
            '<span class="review-flag">待复习</span>'
            if step["number"] in progress["review_step_numbers"]
            else ""
        )
        branch_rows: list[str] = []
        for branch in step["branches"]:
            link = (
                f'<a class="branch-link" href="{esc(branch["file"])}">进入</a>'
                if branch["file"]
                else '<span class="branch-link is-disabled">未开始</span>'
            )
            branch_rows.append(
                f'<li class="branch-row">'
                f'<span class="branch-title">{esc(branch["title"])}</span>'
                f'{status_badge_html(branch["status"])}{link}</li>'
            )
        branches_html = (
            f'<ul class="branch-list">{"".join(branch_rows)}</ul>'
            if branch_rows
            else '<div class="empty-state">该节点尚未细分分支。</div>'
        )
        chunks.append(
            f'<details class="bus-node status-{esc(step["status"])}" '
            f'data-step="{step["number"]}"{open_attr}{current_attr}>'
            '<summary class="bus-node-head">'
            f'<span class="bus-dot">{step["number"]}</span>'
            '<span class="bus-node-copy">'
            f'<strong>{esc(step["title"])}</strong>'
            f'<small>{esc(step["chapter"])}</small></span>'
            f'{review_flag}{status_badge_html(step["status"])}</summary>'
            f'{branches_html}</details>'
        )
    chunks.append("</div></div>")
    return "".join(chunks)


def progress_dashboard_html(progress: dict[str, Any]) -> str:
    advance = percent(progress["touched"], progress["total"])
    mastery = percent(progress["mastered_weight"], progress["total"])
    summary = (
        '<section class="overview-hero" aria-labelledby="overview-title">'
        '<div>'
        '<p class="eyebrow">全课程视图</p>'
        '<h2 id="overview-title">学习到哪里，掌握到什么程度</h2>'
        f'<p>{esc(progress["next_milestone"])}</p>'
        "</div>"
        '<div class="overview-score">'
        f'<strong>{esc(format_number(percent(progress["mastered_weight"], progress["total"])))}%</strong>'
        '<span>验收掌握度</span></div>'
        "</section>"
        '<div class="overview-metrics">'
        '<div><span>课程推进</span>'
        f'<strong>{esc(progress["touched"])} / {esc(progress["total"])}</strong>'
        f'<div class="mini-track"><span style="width:{format_number(advance)}%"></span></div></div>'
        '<div><span>已掌握</span>'
        f'<strong>{esc(progress["mastered_count"])} 步</strong>'
        f'<small>加权 {esc(format_number(progress["mastered_weight"]))} / {esc(progress["total"])}</small>'
        f'<div class="mini-track"><span class="is-mastery" style="width:{format_number(mastery)}%"></span></div></div>'
        '<div><span>待复习</span>'
        f'<strong>{esc(len(progress["active_reviews"]))} 项</strong>'
        '<small>连续两次独立答对后移出</small></div>'
        "</div>"
        '<div class="next-action">'
        '<div class="next-action-copy"><span>下一步建议</span>'
        f'<strong>{esc(progress["next_action"])}</strong></div>'
        f'<small>{esc(progress["next_action_reason"])}</small></div>'
    )

    if progress["active_reviews"]:
        review_rows = "".join(
            '<tr>'
            f'<td>{esc(item["concept"])}</td>'
            f'<td>第 {esc(item["source_step"])} 步</td>'
            f'<td>{esc(item["due"])}</td>'
            f'<td>{esc(item["correct_streak"])} 次</td>'
            "</tr>"
            for item in progress["active_reviews"]
        )
        review_html = (
            '<div class="table-wrap"><table><thead><tr>'
            '<th>概念</th><th>来源</th><th>到期</th><th>连续答对</th>'
            f"</tr></thead><tbody>{review_rows}</tbody></table></div>"
        )
    else:
        review_html = '<div class="empty-state">当前没有待复习概念。</div>'

    acceptance_rows = "".join(
        '<tr>'
        f'<td>{esc(item["date"])}</td>'
        f'<td>{esc(item["step"])}</td>'
        f'<td>{esc(item["concept"])}</td>'
        f'<td>{esc(item["result"])}</td>'
        f'<td>{esc(item["hint_level"])}</td>'
        f'<td>{esc(item["error_type"])}</td>'
        "</tr>"
        for item in progress["acceptance"][-5:]
    )
    acceptance_html = (
        '<div class="table-wrap"><table><thead><tr>'
        '<th>日期</th><th>步骤</th><th>概念</th><th>结果</th><th>提示层级</th><th>错误类型</th>'
        f"</tr></thead><tbody>{acceptance_rows}</tbody></table></div>"
        if acceptance_rows
        else '<div class="empty-state">尚无验收记录。</div>'
    )

    weak_html = (
        '<div class="weak-tags">'
        + "".join(f'<span>{esc(item)}</span>' for item in progress["weak_points"])
        + "</div>"
        if progress["weak_points"]
        else '<div class="empty-state">暂无记录的薄弱点。</div>'
    )

    return (
        '<div class="progress-dashboard" data-progress-dashboard="" '
        f'data-progress-advance="{format_number(advance)}" '
        f'data-progress-mastery="{format_number(mastery)}">'
        + summary
        + '<h2 id="course-map">课程主线</h2>'
        + course_bus_html(progress)
        + '<h2 id="review-queue">复习队列</h2>'
        + review_html
        + '<h2 id="weak-points">当前薄弱点</h2>'
        + weak_html
        + '<h2 id="acceptance-history">最近验收</h2>'
        + acceptance_html
        + f'<div class="overview-footnote"><span>N+2 备课：第 {esc(progress["prepared_step"])} 步已备</span>'
        + f'<span>状态更新 {esc(progress["last_updated"])}</span></div>'
        + "</div>"
    )


def nav_html(groups: list[dict[str, Any]], documents: list[dict[str, Any]], active: str | None) -> str:
    chunks: list[str] = []
    for group in groups:
        chunks.append('<div class="nav-group">')
        chunks.append(f'<p class="nav-group-title">{esc(group["title"])}</p>')
        for doc in (item for item in documents if item["group"] == group["id"]):
            active_class = " is-active" if doc["id"] == active else ""
            current = ' aria-current="page"' if doc["id"] == active else ""
            chunks.append(
                f'<a class="side-link{active_class}" href="{esc(doc["file"])}"{current}>'
                f'<span class="side-icon" aria-hidden="true">{esc(doc["icon"])}</span>'
                f'<span>{esc(doc["title"])}</span></a>'
            )
        chunks.append("</div>")
    return "\n".join(chunks)


def document_cards_html(documents: list[dict[str, Any]]) -> str:
    chunks: list[str] = []
    for doc in documents:
        badge = (
            f'<span class="badge">{esc(doc["badge"])}</span>' if doc["badge"] else ""
        )
        chunks.append(
            '<article class="doc-card">'
            f'<div class="doc-card-top"><span class="doc-icon" aria-hidden="true">'
            f'{esc(doc["icon"])}</span>{badge}</div>'
            f'<h3>{esc(doc["title"])}</h3>'
            f'<p>{esc(doc["description"])}</p>'
            f'<a class="entry-button" href="{esc(doc["file"])}">'
            f'{esc(doc["entry_label"])}<span aria-hidden="true">→</span></a>'
            "</article>"
        )
    return "\n".join(chunks)


def index_groups_html(groups: list[dict[str, Any]], documents: list[dict[str, Any]]) -> str:
    chunks: list[str] = []
    for group in groups:
        docs = [item for item in documents if item["group"] == group["id"]]
        cards = document_cards_html(docs)
        description = (
            f'<p class="group-description">{esc(group["description"])}</p>'
            if group["description"]
            else ""
        )
        if group["display"] == "collapsed":
            summary_desc = (
                f" · {esc(group['description'])}" if group["description"] else ""
            )
            chunks.append('<details class="doc-more">')
            chunks.append(
                '<summary class="more-toggle">'
                f'<span><strong>{esc(group["title"])}</strong>{summary_desc}</span>'
                f'<span>展开 {len(docs)} 个入口</span></summary>'
            )
            chunks.append(f'<div class="doc-grid">{cards}</div>')
            chunks.append("</details>")
            continue

        chunks.append('<section class="doc-section">')
        chunks.append(
            f'<div class="section-heading"><h2>{esc(group["title"])}</h2>{description}</div>'
        )
        chunks.append(f'<div class="doc-grid">{cards}</div>')
        chunks.append("</section>")
    return "\n".join(chunks)


def build_document(
    template: str,
    course: dict[str, Any],
    groups: list[dict[str, Any]],
    documents: list[dict[str, Any]],
    progress: dict[str, Any],
    index: int,
) -> str:
    doc = documents[index]
    group = next(item for item in groups if item["id"] == doc["group"])
    previous_doc = documents[index - 1] if index > 0 else None
    next_doc = documents[index + 1] if index + 1 < len(documents) else None

    if previous_doc:
        previous_link = (
            f'<a class="page-nav-link" href="{esc(previous_doc["file"])}">'
            f'<span>上一份</span><strong>{esc(previous_doc["title"])}</strong></a>'
        )
    else:
        previous_link = '<span class="page-nav-link is-disabled"><span>上一份</span><strong>已是第一篇</strong></span>'

    if next_doc:
        next_link = (
            f'<a class="page-nav-link align-right" href="{esc(next_doc["file"])}">'
            f'<span>下一份</span><strong>{esc(next_doc["title"])}</strong></a>'
        )
    else:
        next_link = '<span class="page-nav-link align-right is-disabled"><span>下一份</span><strong>已是最后一篇</strong></span>'

    badge = (
        f'<span class="badge">{esc(doc["badge"])}</span>' if doc["badge"] else ""
    )
    body = doc["body"]
    if doc["kind"] == "progress":
        body += "\n" + progress_dashboard_html(progress)
    tokens = {
        "COURSE_TITLE": esc(course["title"]),
        "DOC_TITLE": esc(doc["title"]),
        "DOC_DESCRIPTION": esc(doc["description"]),
        "DOC_KIND": esc(doc["kind"]),
        "GROUP_TITLE": esc(group["title"]),
        "CURRENT_STEP": esc(progress["current_step_number"]),
        "UPDATED": esc(progress["last_updated"]),
        "BADGE": badge,
        "SIDEBAR_NAV": nav_html(groups, documents, doc["id"]),
        "BODY": body,
        "PREVIOUS_LINK": previous_link,
        "NEXT_LINK": next_link,
    }
    return replace_tokens(template, tokens)


def _relpath(path: Path, base: Path) -> str:
    """Return path relative to base when possible, else just the file name.

    Prefer a relative path so generated marker files do not leak machine-specific
    absolute paths.  Falls back to the file name when the two paths are on
    different drives (Windows) or a relative path is not meaningful.
    """
    try:
        rel = path.resolve().relative_to(base.resolve())
        return rel.as_posix()
    except (ValueError, OSError):
        return path.name


def ensure_safe_output(output: Path, allow_existing: bool) -> Path | None:
    output = output.resolve()
    marker = output / MARKER_NAME
    if output.exists() and any(output.iterdir()) and not marker.exists() and not allow_existing:
        raise BuildError(
            f"输出目录非空且不是本生成器创建的站点：{output}\n"
            "请换一个目录，或确认后加 --allow-existing。"
        )
    if marker.exists():
        try:
            previous = json.loads(marker.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None
        pages = previous.get("pages", [])
        return set(item for item in pages if isinstance(item, str))
    return None


def build(manifest_path: Path, output: Path, allow_existing: bool) -> None:
    manifest_path = manifest_path.resolve()
    base = manifest_path.parent
    skill_root = Path(__file__).resolve().parents[1]
    template_root = skill_root / "assets" / "site-template"
    required_templates = [
        template_root / "index-template.html",
        template_root / "document-template.html",
        template_root / "style.css",
        template_root / "app.js",
    ]
    for path in required_templates:
        if not path.is_file():
            raise BuildError(f"缺少站点模板：{path}")

    manifest = read_json(manifest_path)
    course, groups, documents = normalize_manifest(manifest, base)
    progress = load_progress(base, course, documents)
    output = output.resolve()
    previous_pages = ensure_safe_output(output, allow_existing)
    output.mkdir(parents=True, exist_ok=True)

    index_template = (template_root / "index-template.html").read_text(encoding="utf-8")
    document_template = (template_root / "document-template.html").read_text(
        encoding="utf-8"
    )
    notes_doc = next(doc for doc in documents if doc["kind"] == "notes")
    resume_doc = next(
        (
            doc
            for doc in documents
            if progress["current_step_file"]
            and doc["file"] == progress["current_step_file"]
        ),
        notes_doc,
    )
    resume_label = (
        f"继续学习第 {progress['current_step_number']} 步"
        if resume_doc is not notes_doc
        else "从主笔记继续"
    )
    progress_doc = next(doc for doc in documents if doc["kind"] == "progress")

    index_html = replace_tokens(
        index_template,
        {
            "COURSE_TITLE": esc(course["title"]),
            "COURSE_SUMMARY": esc(course["summary"]),
            "COURSE_STATUS": esc(progress["status_label"]),
            "CURRENT_STEP": esc(progress["current_step_number"]),
            "UPDATED": esc(progress["last_updated"]),
            "DOC_COUNT": str(len(documents)),
            "GROUP_COUNT": str(len(groups)),
            "DOC_GROUPS": index_groups_html(groups, documents),
            "SIDEBAR_NAV": nav_html(groups, documents, None),
            "PRIMARY_NOTES_FILE": esc(resume_doc["file"]),
            "PRIMARY_NOTES_LABEL": esc(resume_label),
            "PROGRESS_SNAPSHOT": progress_snapshot_html(progress, progress_doc["file"]),
        },
    )
    (output / "index.html").write_text(index_html, encoding="utf-8")

    for index, doc in enumerate(documents):
        page = build_document(
            document_template, course, groups, documents, progress, index
        )
        (output / doc["file"]).write_text(page, encoding="utf-8")

    assets_dir = output / "assets"
    assets_dir.mkdir(exist_ok=True)
    shutil.copy2(template_root / "style.css", assets_dir / "style.css")
    shutil.copy2(template_root / "app.js", assets_dir / "app.js")

    source_assets = base / "content" / "assets"
    if source_assets.is_dir():
        course_assets = assets_dir / "course"
        shutil.copytree(source_assets, course_assets, dirs_exist_ok=True)

    generated_pages = {doc["file"] for doc in documents}
    if previous_pages:
        for stale in sorted(previous_pages.difference(generated_pages)):
            target = (output / stale).resolve()
            try:
                target.relative_to(output)
            except ValueError:
                continue
            if target.is_file() and target.parent == output:
                target.unlink()

    marker = {
        "generator": "learning-skill-html",
        "version": 2,
        "manifest": _relpath(manifest_path, output),
        "state": _relpath(progress["state_path"], output),
        "pages": sorted(generated_pages),
        "updated": course["updated"],
    }
    (output / MARKER_NAME).write_text(
        json.dumps(marker, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    print(f"已生成：{output / 'index.html'}")
    print(f"文档页面：{len(documents)}；分组：{len(groups)}")


def main() -> int:
    args = parse_args()
    try:
        build(args.manifest, args.output, args.allow_existing)
    except BuildError as exc:
        print(f"生成失败：{exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
