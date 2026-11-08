#!/usr/bin/env python3
"""Validate links, navigation coverage, and offline constraints for a generated site."""

from __future__ import annotations

import argparse
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

MARKER_NAME = ".learning-skill-html.json"
REMOTE = re.compile(r"^(?:https?:)?//", re.IGNORECASE)


class LinkCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[tuple[str, str]] = []
        self.ids: set[str] = set()
        self.external_resources: list[str] = []
        self.demo_count = 0
        self.progress_snapshots = 0
        self.progress_dashboards = 0
        self.course_bus = 0
        self.bus_nodes = 0
        self.progress_snapshot_values: list[tuple[str, str]] = []
        self.progress_dashboard_values: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        element_id = values.get("id")
        if element_id:
            self.ids.add(element_id)
        for attr in ("href", "src"):
            value = values.get(attr)
            if value:
                self.links.append((tag, value))
                if REMOTE.match(value):
                    self.external_resources.append(f"{tag}[{attr}]={value}")
        if "data-demo" in values or "data-quiz" in values:
            self.demo_count += 1
        classes = set((values.get("class") or "").split())
        if "progress-snapshot" in classes:
            self.progress_snapshots += 1
            self.progress_snapshot_values.append(
                (
                    values.get("data-progress-advance", ""),
                    values.get("data-progress-mastery", ""),
                )
            )
        if "data-progress-dashboard" in values:
            self.progress_dashboards += 1
            self.progress_dashboard_values.append(
                (
                    values.get("data-progress-advance", ""),
                    values.get("data-progress-mastery", ""),
                )
            )
        if "course-bus" in classes:
            self.course_bus += 1
        if "bus-node" in classes:
            self.bus_nodes += 1


def parse_page(path: Path) -> LinkCollector:
    collector = LinkCollector()
    collector.feed(path.read_text(encoding="utf-8"))
    return collector


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate an offline learning site.")
    parser.add_argument("site", type=Path)
    args = parser.parse_args()
    site = args.site.resolve()
    errors: list[str] = []
    warnings: list[str] = []

    marker_path = site / MARKER_NAME
    if not marker_path.is_file():
        print(f"校验失败：缺少生成标记 {marker_path}", file=sys.stderr)
        return 1
    try:
        marker = json.loads(marker_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"校验失败：生成标记不是有效 JSON：{exc}", file=sys.stderr)
        return 1

    pages = marker.get("pages")
    if not isinstance(pages, list) or not pages:
        print("校验失败：生成标记没有 pages。", file=sys.stderr)
        return 1

    expected_pages = ["index.html", *pages]
    parsed: dict[str, LinkCollector] = {}
    for name in expected_pages:
        path = site / name
        if not path.is_file():
            errors.append(f"缺少页面：{name}")
            continue
        collector = parse_page(path)
        parsed[name] = collector
        if collector.external_resources:
            errors.extend(
                f"{name} 含远程资源：{value}" for value in collector.external_resources
            )

    index = parsed.get("index.html")
    if index:
        hrefs = [value for _, value in index.links]
        for name in pages:
            if name not in hrefs:
                errors.append(f"首页缺少文档入口：{name}")
        if index.progress_snapshots != 1:
            errors.append("首页必须包含一个学习概况摘要")

    for name, collector in parsed.items():
        for tag, href in collector.links:
            if href.startswith(("#", "mailto:", "tel:", "data:")):
                continue
            split = urlsplit(href)
            if split.scheme or split.netloc:
                continue
            target_text = unquote(split.path)
            if not target_text:
                continue
            target = (site / target_text).resolve()
            try:
                target.relative_to(site)
            except ValueError:
                errors.append(f"{name} 链接越过站点目录：{href}")
                continue
            if not target.exists():
                errors.append(f"{name} 断链：{href}")
                continue
            if split.fragment and target.is_file() and target.suffix.lower() == ".html":
                target_page = parsed.get(target.relative_to(site).as_posix())
                if target_page and split.fragment not in target_page.ids:
                    errors.append(f"{name} 锚点不存在：{href}")

    for name in pages:
        collector = parsed.get(name)
        if collector and "index.html" not in [href for _, href in collector.links]:
            errors.append(f"{name} 缺少返回 index.html 的链接")

    if not (site / "assets" / "style.css").is_file():
        errors.append("缺少 assets/style.css")
    if not (site / "assets" / "app.js").is_file():
        errors.append("缺少 assets/app.js")

    dashboard_total = sum(
        collector.progress_dashboards for collector in parsed.values()
    )
    if dashboard_total != 1:
        errors.append(f"站点必须且只能包含一个学习概况页，实际 {dashboard_total} 个")
    snapshot_values = [
        value
        for collector in parsed.values()
        for value in collector.progress_snapshot_values
    ]
    dashboard_values = [
        value
        for collector in parsed.values()
        for value in collector.progress_dashboard_values
    ]
    if snapshot_values and dashboard_values and snapshot_values[0] != dashboard_values[0]:
        errors.append("首页学习概况与完整概况页的进度数值不一致")
    bus_total = sum(collector.course_bus for collector in parsed.values())
    node_total = sum(collector.bus_nodes for collector in parsed.values())
    if bus_total != 1 or node_total < 1:
        errors.append(
            f"课程主线必须且只能有一个总线并包含节点，实际总线 {bus_total}，节点 {node_total}"
        )

    text_bytes = sum(path.stat().st_size for path in site.rglob("*") if path.is_file())
    if text_bytes > 25 * 1024 * 1024:
        warnings.append(f"站点超过 25 MB：{text_bytes / 1024 / 1024:.1f} MB")

    if errors:
        print("校验失败：", file=sys.stderr)
        for item in errors:
            print(f"- {item}", file=sys.stderr)
        return 1

    demo_total = sum(collector.demo_count for collector in parsed.values())
    print(
        f"校验通过：{len(pages)} 份文档，首页入口与学习概况完整，"
        f"动态组件 {demo_total} 个。"
    )
    for item in warnings:
        print(f"警告：{item}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
