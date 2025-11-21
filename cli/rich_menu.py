"""Lightweight Rich-based prompt helper used as a nicer fallback menu.

Provides a single function `choice(options, title=None, footer=None)` which renders
options using Rich and prompts the user for a numeric selection. Returns the
selected index (0-based) or None for cancel.
"""
from __future__ import annotations

from typing import Iterable, List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


def choice(options: Iterable[str], title: Optional[str] = None, footer: Optional[str] = None) -> Optional[int]:
    """Render a selectable list and prompt for a numeric choice.

    - options: iterable of string labels
    - title: optional panel title
    - footer: optional instructions shown under the table

    Returns the selected 0-based index, or None if the user cancels.
    """
    opts: List[str] = list(options)
    table = Table(expand=True, show_header=False)
    table.add_column("#", justify="right", style="bold yellow", width=4)
    table.add_column("Option")
    for idx, opt in enumerate(opts, start=1):
        table.add_row(str(idx), opt)

    panel = Panel(table, title=title or "", subtitle=footer or "", border_style="cyan")
    console.print(panel)

    # Prompt the user; blank input means cancel
    try:
        raw = console.input("[bold yellow]Select an option (blank to cancel): [/bold yellow]")
    except (EOFError, KeyboardInterrupt):
        return None
    raw = raw.strip()
    if not raw:
        return None
    try:
        val = int(raw)
    except ValueError:
        console.print("[red]Invalid selection.[/red] Please enter a number corresponding to an option.")
        return None
    if val < 1 or val > len(opts):
        console.print("[red]Selection out of range.[/red]")
        return None
    return val - 1
