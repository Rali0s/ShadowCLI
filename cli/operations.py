"""Operations manual display module."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from .content import load_markdown_document


def run(*, console: Console | None = None) -> None:
    try:
        document = load_markdown_document("ops-manual")
    except FileNotFoundError as exc:  # pragma: no cover - defensive fallback
        if console is not None:
            console.print(f"[bold red]{exc}[/bold red]")
        else:
            print(str(exc))
        return

    if console is not None:
        renderable = Panel(
            Text(document, style="white"),
            title="Operations Manual",
            subtitle="Press Enter to return or type 'q' to quit the shell.",
            border_style="cyan",
            padding=(1, 2),
            expand=True,
        )
        console.print(renderable)
        return

    print(document)
    print()
