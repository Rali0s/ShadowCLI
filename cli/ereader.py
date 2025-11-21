"""Terminal E-Reader with optional ANSI (Rich) rendering or a curses pager.

This module provides `display_markdown(path, mode=None)` which can render a
markdown file with colored ANSI output (using Rich) or show the original
curses-based pager with vim-like navigation.

Modes:
- "ansi": Use Rich to render colored Markdown and open it in a pager (uses
  the system pager if available via ``Console.pager()``).
- "curses": Use the original curses-based pager (no ANSI colors, full vim
  like navigation).
- None (auto): Prefer curses when a TTY with curses is available unless the
  environment forces ANSI via ``E_READER_FORCE_ANSI=1`` or ``E_READER_MODE=ansi``.

This keeps the original smooth navigation while adding a colored ANSI
rendering option that works in ANSI-capable terminals.
"""
from __future__ import annotations

from pathlib import Path
from typing import List
import os
import sys
import re


def _truncate_ansi_line(s: str, width: int) -> str:
    """Truncate a string containing ANSI escape sequences to a visible width.

    Keeps ANSI escape sequences intact and does not cut them in the middle. The
    returned string will contain the same escape sequences but the visible
    characters will be limited to `width`.
    """
    # Regex to match ANSI CSI sequences like \x1b[31m or \x1b[0;1m
    ansi_re = re.compile(r"(\x1b\[[0-9;]*[mKHF])")

    parts = ansi_re.split(s)
    visible = 0
    out_parts: list[str] = []

    for part in parts:
        if not part:
            continue
        if ansi_re.match(part):
            # ANSI escape sequence — keep it but does not add to visible width
            out_parts.append(part)
            continue
        # Plain text chunk
        if visible + len(part) <= width:
            out_parts.append(part)
            visible += len(part)
        else:
            remaining = max(0, width - visible)
            if remaining > 0:
                out_parts.append(part[:remaining])
                visible += remaining
            break

    # Ensure reset sequence at end so terminal attributes don't leak
    result = "".join(out_parts)
    if "\x1b[0m" not in result:
        result += "\x1b[0m"
    return result


def _render_markdown_to_lines(path: Path, width: int = 80) -> List[str]:
    from rich.console import Console
    from rich.markdown import Markdown

    console = Console(record=True, width=width)
    text = path.read_text(encoding="utf-8")
    md = Markdown(text, code_theme="monokai")
    with console.capture() as capture:
        console.print(md)
    captured = capture.get()
    # Split into lines. Console.capture returns a single string; preserve lines.
    lines = captured.splitlines()
    return lines


def _rich_ansi_pager(path: Path) -> None:
    """Render the markdown with Rich and open it in an ANSI-capable pager.

    This uses Rich's Console.pager() which falls back to printing if a pager
    isn't available. Colors will be preserved when the terminal supports them.
    """
    from rich.console import Console
    from rich.markdown import Markdown

    console = Console(color_system="truecolor")
    text = path.read_text(encoding="utf-8")
    md = Markdown(text, code_theme="monokai")
    try:
        # Console.pager will invoke the system pager (less) with -R where
        # available so ANSI colors are preserved. If that fails we still
        # print directly to the console which keeps colors.
        with console.pager():
            console.print(md)
    except Exception:
        console.print(md)


def _ansi_inprocess_pager(path: Path) -> None:
    """Render markdown to ANSI escapes and provide an in-process pager.

    This writes a forced-ANSI rendering to a temporary file, reads the
    resulting lines (including ANSI escape sequences), and implements a
    small pager loop using raw terminal input and ANSI cursor control. This
    avoids relying on an external `less` pager and keeps navigation
    responsive in-process.
    """
    import tempfile
    import shutil
    import termios
    import tty
    import select
    import os
    import sys

    from rich.console import Console
    from rich.markdown import Markdown

    # Render to a temp file, forcing terminal output so ANSI escapes are emitted.
    tf = tempfile.NamedTemporaryFile(mode="w+", delete=False, encoding="utf-8")
    try:
        console = Console(file=tf, force_terminal=True, color_system="truecolor")
        text = path.read_text(encoding="utf-8")
        md = Markdown(text, code_theme="monokai")
        console.print(md)
        tf.flush()
        tf.seek(0)
        content = tf.read()
    finally:
        tf.close()

    lines = content.splitlines()

    size = shutil.get_terminal_size((80, 24))
    height = size.lines
    width = size.columns
    page_h = max(1, height - 1)
    pos = 0

    fd = sys.stdin.fileno()
    old_attr = termios.tcgetattr(fd)
    try:
        tty.setcbreak(fd)
        while True:
            # Clear and render page
            sys.stdout.write("\x1b[2J\x1b[H")
            for i in range(page_h):
                idx = pos + i
                if idx < len(lines):
                    raw = lines[idx]
                    safe = _truncate_ansi_line(raw, width)
                    sys.stdout.write(safe + "\n")
                else:
                    sys.stdout.write("\n")

            status = f"j/k:scroll SPACE:pgdn b:pgup g g:top G:bottom /:search q:quit  {pos+1}/{max(1,len(lines))}"
            sys.stdout.write("\x1b[7m" + status[:width] + "\x1b[0m\n")
            sys.stdout.flush()

            # Non-blocking read with select to allow small timeouts for gg detection
            ch = sys.stdin.read(1)
            if not ch:
                continue
            if ch == "q":
                break
            elif ch == "j":
                pos = min(pos + 1, max(0, len(lines) - page_h))
            elif ch == "k":
                pos = max(pos - 1, 0)
            elif ch == " ":
                pos = min(pos + page_h, max(0, len(lines) - page_h))
            elif ch == "b":
                pos = max(pos - page_h, 0)
            elif ch == "g":
                # support gg
                r, _, _ = select.select([sys.stdin], [], [], 0.25)
                if r:
                    nxt = sys.stdin.read(1)
                    if nxt == "g":
                        pos = 0
            elif ch == "G":
                pos = max(0, len(lines) - page_h)
            elif ch == "/":
                # Read a search string (simple, echoing characters)
                sys.stdout.write("\x1b[K/")
                sys.stdout.flush()
                query_chars: list[str] = []
                while True:
                    c = sys.stdin.read(1)
                    if not c:
                        continue
                    if c in ("\n", "\r"):
                        break
                    if c == "\x7f":  # backspace
                        if query_chars:
                            query_chars.pop()
                            sys.stdout.write("\b \b")
                            sys.stdout.flush()
                        continue
                    query_chars.append(c)
                    sys.stdout.write(c)
                    sys.stdout.flush()
                query = "".join(query_chars)
                if query:
                    for idx in range(pos + 1, len(lines)):
                        if query in lines[idx]:
                            pos = idx
                            break
            else:
                # ignore other keys
                pass
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_attr)
        try:
            os.unlink(tf.name)
        except Exception:
            pass


def _curses_pager(lines: List[str]) -> None:
    import curses

    def _main(stdscr):
        curses.use_default_colors()
        curses.curs_set(0)
        h, w = stdscr.getmaxyx()
        pos = 0
        last_search = ""

        def render():
            stdscr.erase()
            h, w = stdscr.getmaxyx()
            height = h - 1
            for i in range(height):
                idx = pos + i
                if idx >= len(lines):
                    break
                # Safely add a truncated line
                try:
                    stdscr.addnstr(i, 0, lines[idx], w - 1)
                except Exception:
                    pass
            status = f"j/k:scroll SPACE:pgdn b:pgup g g:top G:bottom /:search q:quit  {pos+1}/{max(1,len(lines))}"
            try:
                stdscr.addnstr(h - 1, 0, status, w - 1, curses.A_REVERSE)
            except Exception:
                pass
            stdscr.refresh()

        render()
        while True:
            c = stdscr.get_wch()
            if isinstance(c, str):
                if c == "q":
                    break
                elif c == "j":
                    pos = min(pos + 1, max(0, len(lines) - (h - 1)))
                elif c == "k":
                    pos = max(pos - 1, 0)
                elif c == " ":
                    pos = min(pos + (h - 1), max(0, len(lines) - (h - 1)))
                elif c == "b":
                    pos = max(pos - (h - 1), 0)
                elif c == "g":
                    # support gg to go to top
                    stdscr.nodelay(True)
                    try:
                        nxt = stdscr.get_wch()
                        if nxt == "g":
                            pos = 0
                    except Exception:
                        pass
                    finally:
                        stdscr.nodelay(False)
                elif c == "G":
                    pos = max(0, len(lines) - (h - 1))
                elif c == "/":
                    # prompt for search term
                    curses.echo()
                    try:
                        stdscr.addstr(h - 1, 0, "/")
                        stdscr.clrtoeol()
                        query = stdscr.getstr(h - 1, 1).decode("utf-8")
                    except Exception:
                        query = ""
                    curses.noecho()
                    if query:
                        last_search = query
                        for idx in range(pos + 1, len(lines)):
                            if query in lines[idx]:
                                pos = idx
                                break
                else:
                    # ignore other printable chars
                    pass
            else:
                # handle special keys
                if c == curses.KEY_DOWN:
                    pos = min(pos + 1, max(0, len(lines) - (h - 1)))
                elif c == curses.KEY_UP:
                    pos = max(pos - 1, 0)
                elif c == curses.KEY_NPAGE:
                    pos = min(pos + (h - 1), max(0, len(lines) - (h - 1)))
                elif c == curses.KEY_PPAGE:
                    pos = max(pos - (h - 1), 0)
            render()

    try:
        import curses

        curses.wrapper(_main)
    except Exception as exc:  # fallback if curses fails
        print("Error launching pager:", exc)


def display_markdown(path: str | Path, mode: str | None = None) -> None:
    """Render a markdown file and display it.

    Parameters
    - path: file path to the markdown file
    - mode: one of (None|'ansi'|'curses'). None means auto-detect.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(path)

    # Determine mode precedence: explicit arg > E_READER_MODE env > auto
    if mode is None:
        mode = os.environ.get("E_READER_MODE")

    if not mode:
        force_ansi = os.environ.get("E_READER_FORCE_ANSI", "0").lower() in (
            "1",
            "true",
            "yes",
        )
        curses_available = True
        try:
            import curses  # type: ignore

            # import succeeded
        except Exception:
            curses_available = False

        if force_ansi or not (sys.stdin.isatty() and sys.stdout.isatty() and curses_available):
            mode = "ansi"
        else:
            mode = "curses"

    if mode == "ansi":
        # Prefer the in-process ANSI pager to avoid external pager dependency.
        try:
            _ansi_inprocess_pager(p)
            return
        except Exception:
            # Fallback to the external pager approach if something fails.
            _rich_ansi_pager(p)
            return

    # curses path (original behavior)
    try:
        import shutil

        width = shutil.get_terminal_size((80, 24)).columns
    except Exception:
        width = 80
    lines = _render_markdown_to_lines(p, width=width)
    _curses_pager(lines)
