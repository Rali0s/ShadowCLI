"""Persistent Rich-based menu shell for ShadowOps."""

from __future__ import annotations

import inspect
from dataclasses import dataclass
from typing import Iterable, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

try:  # pragma: no cover - optional dependency guard
    from simple_term_menu import TerminalMenu
except ImportError:  # pragma: no cover - fallback if dependency missing
    TerminalMenu = None  # type: ignore[assignment]

from .navigation import ENTRIES, NavigationEntry

__all__ = ["RichMenuShell", "main"]


@dataclass(frozen=True)
class MenuOption:
    """Represents a selectable navigation option."""

    index: int
    entry: NavigationEntry

    @property
    def label(self) -> str:
        return self.entry.label


class RichMenuShell:
    """Interactive menu rendered with Rich that loops until exit."""

    def __init__(self, console: Optional[Console] = None) -> None:
        self.console = console or Console()
        self._options: list[MenuOption] = [
            MenuOption(idx, entry) for idx, entry in enumerate(ENTRIES, start=1)
        ]

    # ------------------------------------------------------------------
    # Rendering helpers
    # ------------------------------------------------------------------

    def _menu_panel(self) -> Panel:
        table = Table(expand=True, show_header=True, header_style="bold cyan")
        table.add_column("#", justify="right", style="bold yellow")
        table.add_column("Module")
        for option in self._options:
            table.add_row(str(option.index), option.label)

        table.add_section()
        table.add_row("R", "Run all modules")
        table.add_row("Q", "Quit ShadowOps")

        subtitle = (
            "Enter a number to launch a module, R to run all, or Q to exit."
        )
        return Panel(
            table,
            title="ShadowOps Persistent Shell",
            subtitle=subtitle,
            border_style="magenta",
        )

    def _render_menu(self) -> None:
        self.console.print(self._menu_panel())

    def _menu_title(self) -> str:
        """Render the Rich panel to a captured string for terminal menus."""

        with self.console.capture() as capture:
            self.console.print(self._menu_panel())
        return capture.get()

    def _terminal_menu_entries(self) -> list[str]:
        entries = [f"{option.index}. {option.label}" for option in self._options]
        entries.append("Run all modules")
        entries.append("Quit ShadowOps shell")
        return entries

    def _show_terminal_menu(self) -> Optional[int]:
        """Display the simple-term-menu selector when available."""

        if TerminalMenu is None:
            return None

        menu = TerminalMenu(
            self._terminal_menu_entries(),
            title=self._menu_title(),
            clear_screen=True,
            cycle_cursor=True,
            menu_cursor_style=("fg_yellow", "bold"),
            menu_highlight_style=("fg_cyan", "bold"),
        )
        selected = menu.show()
        if selected is None:
            return None
        return int(selected)

    # ------------------------------------------------------------------
    # Command execution
    # ------------------------------------------------------------------

    def _call_handler(self, option: MenuOption) -> None:
        handler = option.entry.handler

        try:
            signature = inspect.signature(handler)
        except (TypeError, ValueError):
            signature = None

        if signature is not None:
            parameters = signature.parameters.values()
            accepts_console = any(
                parameter.kind is inspect.Parameter.VAR_KEYWORD
                or parameter.name == "console"
                for parameter in parameters
            )
            if accepts_console:
                handler(console=self.console)
                return

        handler()

    def _prompt_after_module(self) -> bool:
        prompt = Panel.fit(
            "[bold yellow]Press Enter to return to the main menu.[/bold yellow]\n"
            "[bold magenta]Type 'q' to quit the ShadowOps shell.[/bold magenta]",
            border_style="bright_black",
        )
        self.console.print(prompt)

        while True:
            response = self.console.input("[bold yellow]Command[/bold yellow]: ")
            normalized = response.strip().lower()
            if normalized in {"", "continue", "c"}:
                return False
            if normalized in {"q", "quit", "exit"}:
                return True
            self.console.print(
                "[bold red]Invalid response.[/bold red] Press Enter or type 'q' to quit."
            )

    def _run_entry(self, option: MenuOption, *, pause: bool = True) -> bool:
        self.console.print(
            f"\n[bold green]► Launching[/bold green] {option.label}...",
            highlight=False,
        )
        self.console.rule(f"[bold cyan]{option.label}[/bold cyan]", style="cyan")
        try:
            self._call_handler(option)
        except Exception as exc:  # pragma: no cover - defensive fallback
            self.console.print(
                Panel(
                    f"Module '[bold]{option.label}[/bold]' failed: {exc}",
                    title="Module Error",
                    border_style="red",
                )
            )
        finally:
            self.console.rule(style="cyan")

        if not pause:
            return False

        return self._prompt_after_module()

    def _resolve_selection(self, selection: str) -> Optional[MenuOption]:
        normalized = selection.strip().lower()
        if not normalized:
            return None
        for option in self._options:
            if normalized == str(option.index) or normalized == option.label.lower():
                return option
        return None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def list_modules(self) -> None:
        """Display the menu once without entering the loop."""

        self._render_menu()

    def run_all(self) -> None:
        """Run every module sequentially."""

        self.console.print("\n[bold blue]Running all modules sequentially...[/bold blue]")
        for option in self._options:
            self._run_entry(option, pause=False)

    def run_selection(self, selector: str) -> bool:
        """Execute a single selection provided via CLI options."""

        if selector.lower() in {"r", "run", "run all", "runall"}:
            self.run_all()
            return True

        option = self._resolve_selection(selector)
        if option is None:
            self.console.print(
                Panel.fit(
                    f"No module matches '[bold]{selector}[/bold]'.",
                    title="Unknown Selection",
                    border_style="red",
                )
            )
            return False

        self._run_entry(option, pause=False)
        return True

    def _fallback_loop(self) -> None:
        """Text-based prompt loop when simple-term-menu is unavailable."""

        while True:
            self._render_menu()
            choice = self.console.input(
                "[bold yellow]Select an option[/bold yellow] ([green]q[/green]/[green]quit[/green] to exit): "
            )
            lowered = choice.strip().lower()
            if lowered in {"q", "quit", "exit"}:
                self.console.print("\n[bold magenta]Goodbye![/bold magenta]")
                return
            if lowered in {"r", "run", "run all", "runall"}:
                self.run_all()
                continue

            option = self._resolve_selection(choice)
            if option is None:
                self.console.print(
                    Panel.fit(
                        "Unknown selection. Choose an index or module name.",
                        border_style="red",
                    )
                )
                continue

            if self._run_entry(option):
                self.console.print("\n[bold magenta]Goodbye![/bold magenta]")
                return

    def loop(self) -> None:
        """Prompt the user repeatedly until they choose to exit."""

        if TerminalMenu is None:
            self._fallback_loop()
            return

        while True:
            selection = self._show_terminal_menu()
            if selection is None:
                self.console.print("\n[bold magenta]Goodbye![/bold magenta]")
                return

            if selection == len(self._options):
                self.run_all()
                continue
            if selection == len(self._options) + 1:
                self.console.print("\n[bold magenta]Goodbye![/bold magenta]")
                return

            option = self._options[selection]
            if self._run_entry(option):
                self.console.print("\n[bold magenta]Goodbye![/bold magenta]")
                return


def main(argv: Optional[Iterable[str]] = None) -> int:
    """Console-script entry point for the persistent Rich shell."""

    import argparse

    parser = argparse.ArgumentParser(
        prog="shadowops-rich-shell",
        description="Persistent Rich-rendered shell for the ShadowOps toolkit.",
    )
    parser.add_argument(
        "-m",
        "--module",
        dest="module",
        help="Run a single module by number or name and exit.",
    )
    parser.add_argument(
        "-r",
        "--run-all",
        dest="run_all",
        action="store_true",
        help="Run all modules sequentially and exit.",
    )
    parser.add_argument(
        "--list",
        dest="list_only",
        action="store_true",
        help="List available modules and exit.",
    )

    args = parser.parse_args(list(argv) if argv is not None else None)
    shell = RichMenuShell()

    if args.list_only:
        shell.list_modules()
        return 0
    if args.run_all:
        shell.run_all()
        return 0
    if args.module:
        success = shell.run_selection(args.module)
        return 0 if success else 2

    try:
        shell.loop()
    except KeyboardInterrupt:  # pragma: no cover - interactive guard
        shell.console.print("\n[bold red]Interrupted by user.[/bold red]")
        return 130
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
