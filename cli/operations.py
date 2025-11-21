"""Operations manual display module.

This module now opens the operations manual inside an interactive panel
viewer (so the Cement shell entry doesn't print the whole document and
cause scroll). The implementation delegates to `cli.manuals.display_manual_panel`.
"""

from __future__ import annotations

from pathlib import Path

from . import get_content_path

def run() -> None:
    path = get_content_path() / "ops-manual.md"
    if not path.exists():
        print(f"Operations manual not found at {path}")
        return
    try:
        # Import locally to avoid heavier imports at module import time
        from .manuals import display_manual_panel

        display_manual_panel(path)
    except Exception:
        # Fallback: print the document if interactive viewer fails
        try:
            from .content import load_markdown_document

            print(load_markdown_document("ops-manual"))
        except Exception as exc:
            print(f"Could not open operations manual: {exc}")
