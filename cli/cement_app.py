"""Cement-powered persistent menu shell for ShadowOps."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional
import os
from pathlib import Path
import termios
import tty
import shutil
import sys
import select

from cement import App, Controller, ex
from cement.utils.misc import minimal_logger
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.theme import Theme
from rich.text import Text

from .navigation import ENTRIES, NavigationEntry

__all__ = ["ShadowOpsApp", "main"]

LOGGER = minimal_logger(__name__)
# Use a dark-deep blue themed Console for the persistent shell
_THEME = Theme({
    "menu.border": "deep_sky_blue4",
    "menu.title": "bright_white",
    "menu.subtitle": "grey66",
})
CONSOLE = Console(theme=_THEME)


@dataclass(frozen=True)
class MenuOption:
    """Represents a menu entry available to the user."""

    index: int
    entry: NavigationEntry

    @property
    def label(self) -> str:
        return self.entry.label


class MenuShell:
    """Interactive loop that keeps the ShadowOps toolkit alive."""

    def __init__(self, console: Console = CONSOLE) -> None:
        self._console = console
        # Reader mode preference: None == auto, otherwise 'ansi' or 'curses'
        self.reader_mode: Optional[str] = os.environ.get("E_READER_MODE")

    def _build_options(self) -> List[MenuOption]:
        """Build current menu options, inserting the Reader Mode setting at the top.

        This is rebuilt each loop so the label can reflect the current setting.
        """
        opts: List[MenuOption] = []
        # Reader Mode option at position 1
        reader_label = f"Reader Mode: {self.reader_mode or 'auto'}"
        opts.append(MenuOption(1, NavigationEntry(reader_label, self._prompt_reader_mode)))
        # Append the regular entries after the Reader Mode option
        for idx, entry in enumerate(ENTRIES, start=2):
            opts.append(MenuOption(idx, entry))
        # Add a Manuals Browser option as the last item
        opts.append(MenuOption(len(opts) + 1, NavigationEntry("Manuals Browser", self.browse_manuals)))
        return opts

    # ------------------------------------------------------------------
    # Manuals browser (in-panel pager)
    # ------------------------------------------------------------------

    def _manuals_root(self) -> Path:
        # Import `get_content_path` robustly: prefer absolute import when running as
        # a top-level module, fall back to a relative import when the package
        # layout provides it.
        try:
            from cli import get_content_path
        except Exception:
            from .. import get_content_path

        return get_content_path() / "manuals_data"

    def _choose_manual(self) -> Optional[Path]:
        """List manuals and let the user pick a section file.

        Returns the chosen Path or None if cancelled.
        """
        root = self._manuals_root()
        if not root.exists():
            self._console.print(Panel(f"Manuals directory not found: {root}", title="Manuals", border_style="red"))
            return None

        manuals = sorted([p for p in root.iterdir() if p.is_dir()], key=lambda p: p.name.lower())
        options: list[Path] = []
        for m in manuals:
            for sec in sorted(m.glob("*.md"), key=lambda p: p.name.lower()):
                options.append(sec)

        if not options:
            self._console.print(Panel("No manual sections found.", title="Manuals", border_style="yellow"))
            return None

        # Render a compact list and prompt for numeric selection.
        lines = []
        for idx, p in enumerate(options, start=1):
            lines.append(f"{idx}. {p.parent.name} / {p.name}")

        self._console.print(Panel("\n".join(lines), title="Manual Sections", border_style="menu.border", padding=(1,2)))
        choice = self._console.input("Enter section number (blank to cancel): ").strip()
        if not choice:
            return None
        try:
            i = int(choice)
            if 1 <= i <= len(options):
                return options[i - 1]
        except Exception:
            pass
        self._console.print("[bold red]Invalid selection.[/bold red]")
        return None

    def _panel_pager(self, lines: list[str], title: str | None = None) -> None:
        """Show `lines` inside a Rich Panel and allow single-key scrolling.

        Keys: j/k, SPACE, b, gg, G, / (search), q to quit.
        """
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        pos = 0
        try:
            tty.setcbreak(fd)
            # use console.size so paging matches available area inside the panel
            page_h = max(1, self._console.size.height - 4)
            last_search = ""
            while True:
                # clamp pos
                pos = min(pos, max(0, len(lines) - page_h))
                visible = lines[pos : pos + page_h]
                body = "\n".join(visible)

                # decode ANSI into Rich Text if present
                if "\x1b" in body:
                    try:
                        rich_body = Text.from_ansi(body)
                    except Exception:
                        rich_body = Text(body)
                else:
                    rich_body = body

                status = f"j/k:scroll SPACE:pgdn b:pgup g g:top G:bottom /:search q:quit  {pos+1}/{max(1,len(lines))}"
                panel = Panel(rich_body, title=title or "Manual", border_style="menu.border", padding=(1,2))
                self._console.clear()
                self._console.print(panel)
                self._console.print(status, style="reverse")

                ch = sys.stdin.read(1)
                if not ch:
                    continue
                if ch == "q":
                    break
                if ch == "j":
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
                    # read a query
                    self._console.print("/", end="")
                    query = self._console.input()
                    if query:
                        last_search = query
                        for idx in range(pos + 1, len(lines)):
                            if query in lines[idx]:
                                pos = idx
                                break
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)

    def browse_manuals(self) -> None:
        """Handler that allows selecting and viewing a manual inside the shell."""
        chosen = self._choose_manual()
        if not chosen:
            return
        # Use ereader's renderer to get pre-rendered lines that respect Markdown
        try:
            from .ereader import _render_markdown_to_lines

            # compute content width so lines fill the panel (panel padding + border = 6)
            content_width = max(20, self._console.size.width - 6)
            lines = _render_markdown_to_lines(chosen, width=content_width)
        except Exception:
            # fallback: raw text
            lines = chosen.read_text(encoding="utf-8").splitlines()

        self._panel_pager(lines, title=f"{chosen.parent.name} / {chosen.name}")

    # ------------------------------------------------------------------
    # Rendering helpers
    # ------------------------------------------------------------------

    def _menu_panel(self) -> Panel:
        table = Table(expand=True, show_header=True, header_style="bold cyan")
        table.add_column("#", justify="right", style="bold yellow")
        table.add_column("Module")
        for option in self._build_options():
            table.add_row(str(option.index), option.label)

        instructions = (
            "[bold]Enter a number[/bold] to launch a module, "
            "[bold]R[/bold] to run all, or [bold]Q[/bold] to exit."
        )
        return Panel(
            table,
            title="ShadowOps Persistent Shell",
            subtitle=instructions,
            border_style="menu.border",
        )

    def _render_menu(self) -> None:
        self._console.print(self._menu_panel())

    # ------------------------------------------------------------------
    # Command dispatch
    # ------------------------------------------------------------------

    def _run_entry(self, option: MenuOption) -> None:
        self._console.print(
            f"\n[bold green]► Launching[/bold green] {option.label}...", highlight=False
        )
        try:
            option.entry.handler()
        except Exception as exc:  # pragma: no cover - defensive guard for handlers
            # MinimalLogger.error in the cement utils accepts (msg, *args) in a limited form
            # to avoid TypeError we format the message here and pass a single string.
            LOGGER.error(f"Module '{option.label}' raised an exception: {exc}")
            self._console.print(
                f"[bold red]Module '{option.label}' failed:[/bold red] {exc}",
            )

    def _run_all(self) -> None:
        self._console.print("\n[bold blue]Running all modules sequentially...[/bold blue]")
        for option in self._build_options()[1:]:
            self._run_entry(option)

    def _resolve_selection(self, selection: str) -> Optional[MenuOption]:
        normalized = selection.strip().lower()
        if not normalized:
            return None
        for option in self._build_options():
            if normalized == str(option.index) or normalized == option.label.lower():
                return option
        return None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def loop(self) -> None:
        """Keep prompting the user until they exit."""
        while True:
            self._render_menu()
            choice = self._console.input(
                "[bold yellow]Select an option[/bold yellow] ([green]q[/green]/[green]quit[/green] to exit): "
            ).strip()
            lowered = choice.lower()
            if lowered in {"q", "quit", "exit"}:
                self._console.print("\n[bold magenta]Goodbye![/bold magenta]")
                return
            if lowered in {"r", "run", "run all", "runall"}:
                self._run_all()
                continue

            option = self._resolve_selection(choice)
            if option is None:
                self._console.print(
                    "[bold red]Unknown selection.[/bold red] Choose an index or module name."
                )
                continue

            # If the user selected the Reader Mode option, the handler will update state.
            self._run_entry(option)

    def _prompt_reader_mode(self) -> None:
        """Prompt user to set the default reader mode for the shell.

        Saves the choice to the environment variable E_READER_MODE so other
        modules pick up the preference when invoked from this shell.
        """
        self._console.print(Panel("Choose default reader mode for manuals:", title="Reader Mode"))
        choice = self._console.input("Enter [bold]auto[/bold]/[bold]ansi[/bold]/[bold]curses[/bold] (blank=auto): ").strip().lower()
        if not choice or choice == "auto":
            self.reader_mode = None
            os.environ.pop("E_READER_MODE", None)
            self._console.print("Reader mode set to [bold]auto[/bold].")
            return
        if choice in {"ansi", "curses"}:
            self.reader_mode = choice
            os.environ["E_READER_MODE"] = choice
            self._console.print(f"Reader mode set to [bold]{choice}[/bold].")
            return
        self._console.print("Unknown choice. No changes made.")

    def run_selection(self, selector: str) -> bool:
        """Execute a single selection when provided via command-line."""

        if selector.lower() in {"r", "run", "run all", "runall"}:
            self._run_all()
            return True

        option = self._resolve_selection(selector)
        if option is None:
            self._console.print(
                f"[bold red]No module matches[/bold red] '{selector}'. "
                "Use `shadowops-cement --list` to view options."
            )
            return False

        self._run_entry(option)
        return True

    def list_modules(self) -> None:
        """Display the menu without entering the loop."""
        self._render_menu()


class BaseController(Controller):
    """Root controller exposing the persistent menu commands."""

    class Meta:
        label = "base"
        description = "ShadowOps Cement interface"
        arguments = [
            (
                ["-m", "--module"],
                {
                    "help": "Run a single module by number or name and exit.",
                    "dest": "module",
                },
            ),
            (
                ["-r", "--run-all"],
                {
                    "help": "Run all modules sequentially and exit.",
                    "action": "store_true",
                    "dest": "run_all",
                },
            ),
            (
                ["--list"],
                {
                    "help": "List available modules and exit.",
                    "action": "store_true",
                    "dest": "list_only",
                },
            ),
        ]

    def _shell(self) -> MenuShell:
        return MenuShell()

    @ex(help="Launch the persistent menu shell (default command).")
    def default(self) -> None:
        pargs = self.app.pargs
        shell = self._shell()

        if getattr(pargs, "list_only", False):
            shell.list_modules()
            return
        if getattr(pargs, "run_all", False):
            shell.run_selection("run")
            return
        if getattr(pargs, "module", None):
            if not shell.run_selection(str(pargs.module)):
                raise SystemExit(2)
            return

        shell.loop()


class ShadowOpsApp(App):
    """Cement application harness for the ShadowOps toolkit."""

    class Meta:
        label = "shadowops"
        base_controller = "base"
        handlers = [BaseController]


def main(argv: Optional[Iterable[str]] = None) -> int:
    """Entry point used by the console script."""

    init_kwargs = {}
    if argv is not None:
        init_kwargs["argv"] = list(argv)

    with ShadowOpsApp(**init_kwargs) as app:
        try:
            app.run()
        except KeyboardInterrupt:  # pragma: no cover - interactive guard
            CONSOLE.print("\n[bold red]Interrupted by user.[/bold red]")
            return 130
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
