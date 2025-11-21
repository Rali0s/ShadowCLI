"""Shared helpers for interactive manual browsing and panel-based viewing.

This module provides a small, self-contained panel pager that other parts of
the CLI (Cement shell, operations runner, Typer commands) can call without
creating circular imports.
"""
from __future__ import annotations

from pathlib import Path
import shutil
import sys
import termios
import tty
import select

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from . import get_content_path
from .ereader import _render_markdown_to_lines


def manuals_root() -> Path:
    return get_content_path() / "manuals_data"


def list_manual_sections() -> list[Path]:
    root = manuals_root()
    if not root.exists():
        return []
    sections: list[Path] = []
    for m in sorted([p for p in root.iterdir() if p.is_dir()], key=lambda p: p.name.lower()):
        for sec in sorted(m.glob("*.md"), key=lambda p: p.name.lower()):
            sections.append(sec)
    return sections


def display_manual_panel(path: Path, console: Console | None = None) -> None:
    """Render the markdown at `path` and display it inside a panel with
    single-key navigation (j/k/space/b/gg/G// /q).
    """
    if console is None:
        console = Console()

    # initial render using console size so we can compute an inner content width
    # that accounts for panel padding and border. Panel uses horizontal padding=2
    # on each side plus a single-character border, so subtract 6 columns.
    content_width = max(20, console.size.width - 6)
    lines = _render_markdown_to_lines(path, width=content_width)

    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    pos = 0
    show_help = False

    # SIGWINCH handling: on resize, recompute lines with new width
    import signal

    resized = False

    def _on_winch(signum, frame):
        nonlocal resized
        resized = True

    prev_winch = signal.getsignal(signal.SIGWINCH)
    signal.signal(signal.SIGWINCH, _on_winch)

    try:
        tty.setcbreak(fd)
        while True:
            if resized:
                # recompute layout for new terminal size using console.size
                content_width = max(20, console.size.width - 6)
                lines = _render_markdown_to_lines(path, width=content_width)
                resized = False

            # compute available page height (leave room for panel padding and status lines)
            page_h = max(1, console.size.height - 6)

            # clamp pos
            pos = min(pos, max(0, len(lines) - page_h))

            visible = lines[pos : pos + page_h]
            body = "\n".join(visible)

            # If the rendered body contains ANSI escapes, decode safely to Rich Text
            if "\x1b" in body:
                try:
                    rich_body = Text.from_ansi(body)
                except Exception:
                    # fallback to plain text if decoding fails
                    rich_body = Text(body)
            else:
                rich_body = body

            status = f"j/k:scroll SPACE:pgdn b:pgup gg:G G:bottom /:search h:help q:quit  {pos+1}/{max(1,len(lines))}"
            panel = Panel(rich_body, title=f"{path.parent.name} / {path.name}", border_style="blue", padding=(1,2))
            console.clear()
            console.print(panel)
            console.print(status, style="reverse")

            if show_help:
                help_text = (
                    "j/k: scroll  SPACE:pgdn  b:pgup  gg:G (go to top)  G:bottom  /:search  h:toggle help  q:quit\n"
                    "Press any navigation key to continue."
                )
                help_panel = Panel(help_text, title="Help", border_style="green")
                console.print(help_panel)

            ch = sys.stdin.read(1)
            if not ch:
                continue
            if ch == "q":
                break
            if ch == "h":
                show_help = not show_help
                continue
            if ch == "j":
                pos = min(pos + 1, max(0, len(lines) - page_h))
            elif ch == "k":
                pos = max(pos - 1, 0)
            elif ch == " ":
                pos = min(pos + page_h, max(0, len(lines) - page_h))
            elif ch == "b":
                pos = max(pos - page_h, 0)
            elif ch == "g":
                r, _, _ = select.select([sys.stdin], [], [], 0.25)
                if r:
                    nxt = sys.stdin.read(1)
                    if nxt == "g":
                        pos = 0
            elif ch == "G":
                pos = max(0, len(lines) - page_h)
            elif ch == "/":
                console.print("/", end="")
                query = console.input()
                if query:
                    for idx in range(pos + 1, len(lines)):
                        if query in lines[idx]:
                            pos = idx
                            break
    finally:
        # restore terminal state and signal handler
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
        try:
            signal.signal(signal.SIGWINCH, prev_winch)
        except Exception:
            pass
