"""Shared content loader for Markdown documents."""

from __future__ import annotations

from pathlib import Path

from . import get_content_path
from .utils.text import render_markdown


class ContentNotFoundError(FileNotFoundError):
    """Raised when a requested content document is missing."""


def load_markdown_document(name: str) -> str:
    """Return the rendered Markdown document located under ``content``.

    Parameters
    ----------
    name:
        Relative document name without extension. Subdirectories can be
        addressed via ``"ops-manual"`` (maps to ``content/ops-manual.md``).
    """

    root = get_content_path()
    path = root / f"{name}.md"
    if not path.exists():
        raise ContentNotFoundError(f"Content document '{name}' not found at {path}")
    return render_markdown(path)
