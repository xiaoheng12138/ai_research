#!/usr/bin/env python3
"""
lint_no_ccg_refs.py - 扫描项目中的 .ccg 引用和绝对路径

用于 CI 验证，确保代码库中不包含硬编码路径。
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import NamedTuple


class LintViolation(NamedTuple):
    file: Path
    line_num: int
    pattern: str
    content: str


# 需要检测的模式
PATTERNS = [
    (re.compile(r"\.ccg[/\\]"), ".ccg/ 目录引用"),
    (re.compile(r"C:[/\\]Users[/\\]", re.IGNORECASE), "Windows 绝对路径 (C:\\Users\\)"),
    (re.compile(r"D:[/\\]", re.IGNORECASE), "Windows 绝对路径 (D:\\)"),
    (re.compile(r"/Users/[a-zA-Z0-9_]+/"), "macOS 绝对路径 (/Users/)"),
    (re.compile(r"/home/[a-zA-Z0-9_]+/"), "Linux 绝对路径 (/home/)"),
]

# 白名单目录/文件（不检查）
WHITELIST_DIRS = {
    ".git",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    "vendor",
    ".claude/plan",  # 计划文档可保留示例
}

WHITELIST_FILES = {
    "de-ccg-cleanup-report.md",  # 清理报告本身
    "lint_no_ccg_refs.py",  # 本脚本
}

# 白名单模式（在这些文件中忽略）
WHITELIST_PATTERNS = {
    "ui-compat.md": [r"D:\\\\ccg-workflow-main"],  # 文档参考
}


def should_skip(path: Path, root: Path) -> bool:
    """判断是否应跳过此路径"""
    rel_path = path.relative_to(root)

    # 检查目录白名单
    for part in rel_path.parts:
        if part in WHITELIST_DIRS:
            return True

    # 检查文件白名单
    if path.name in WHITELIST_FILES:
        return True

    # 只检查文本文件
    if path.suffix.lower() in {".exe", ".dll", ".so", ".dylib", ".pyc", ".pyo", ".png", ".jpg", ".gif", ".ico"}:
        return True

    return False


def scan_file(path: Path, root: Path) -> list[LintViolation]:
    """扫描单个文件"""
    violations: list[LintViolation] = []

    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return violations

    file_whitelist = WHITELIST_PATTERNS.get(path.name, [])

    for line_num, line in enumerate(content.splitlines(), start=1):
        for pattern, description in PATTERNS:
            if pattern.search(line):
                # 检查是否在白名单中
                skip = False
                for wp in file_whitelist:
                    if re.search(wp, line):
                        skip = True
                        break

                if not skip:
                    violations.append(LintViolation(
                        file=path.relative_to(root),
                        line_num=line_num,
                        pattern=description,
                        content=line.strip()[:100],
                    ))

    return violations


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="扫描项目中的 .ccg 引用和绝对路径"
    )
    parser.add_argument(
        "root",
        nargs="?",
        default=".",
        help="项目根目录 (默认: 当前目录)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="严格模式：任何违规都返回非零退出码",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="以 JSON 格式输出",
    )
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"错误: {root} 不是目录", file=sys.stderr)
        return 1

    all_violations: list[LintViolation] = []

    # 扫描所有文件
    for path in root.rglob("*"):
        if path.is_file() and not should_skip(path, root):
            violations = scan_file(path, root)
            all_violations.extend(violations)

    # 输出结果
    if args.json:
        import json
        output = [
            {
                "file": str(v.file),
                "line": v.line_num,
                "pattern": v.pattern,
                "content": v.content,
            }
            for v in all_violations
        ]
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        if all_violations:
            print(f"发现 {len(all_violations)} 处违规:\n")
            for v in all_violations:
                print(f"  {v.file}:{v.line_num}")
                print(f"    模式: {v.pattern}")
                print(f"    内容: {v.content[:80]}...")
                print()
        else:
            print("未发现违规 ✓")

    # 退出码
    if args.strict and all_violations:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
