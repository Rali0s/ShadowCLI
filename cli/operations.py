"""Operations manual display module."""

from __future__ import annotations

from .content import load_markdown_document


def run() -> None:
    try:
        document = load_markdown_document("ops-manual")
    except FileNotFoundError as exc:  # pragma: no cover - defensive fallback
        print(str(exc))
        return
    print(document)
    print()
