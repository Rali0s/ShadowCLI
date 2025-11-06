"""Utilities for rendering formatted text in the terminal."""

from __future__ import annotations

import shutil
import textwrap
from pathlib import Path
from typing import Iterable, List

DEFAULT_WIDTH = 88


def get_terminal_width() -> int:
    width = shutil.get_terminal_size((DEFAULT_WIDTH, 24)).columns
    return max(60, min(width, 120))


def wrap_paragraphs(text: str, width: int | None = None) -> str:
    width = width or get_terminal_width()
    paragraphs = [
        "\n".join(textwrap.fill(line, width=width) if line.strip() else "" for line in chunk.splitlines())
        for chunk in text.split("\n\n")
    ]
    return "\n\n".join(paragraphs)


def render_markdown(path: Path) -> str:
    """Convert a very small subset of Markdown to wrapped plain text."""
    width = get_terminal_width()
    lines = path.read_text(encoding="utf-8").splitlines()
    rendered: List[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            rendered.append("")
            continue
        if stripped.startswith("#"):
            level = len(stripped) - len(stripped.lstrip("#"))
            heading = stripped.lstrip("# ")
            underline = "=" if level == 1 else "-"
            rendered.append(heading.upper() if level == 1 else heading)
            rendered.append(underline * min(len(heading), width))
            continue
        if stripped.startswith("- "):
            bullet = wrap_paragraphs(stripped[2:], width - 4)
            rendered.extend(f"  - {line}" for line in bullet.splitlines())
            continue
        rendered.append(textwrap.fill(stripped, width=width))
    return "\n".join(rendered)


def format_table(rows: Iterable[Iterable[str]]) -> str:
    table = [list(map(str, row)) for row in rows]
    if not table:
        return ""
    widths = [max(len(row[idx]) for row in table) for idx in range(len(table[0]))]
    return "\n".join("  ".join(cell.ljust(widths[idx]) for idx, cell in enumerate(row)) for row in table)
