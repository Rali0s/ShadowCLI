"""Cement-powered persistent menu shell for ShadowOps."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional

from cement import App, Controller, ex
from cement.utils.misc import minimal_logger
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .navigation import ENTRIES, NavigationEntry

__all__ = ["ShadowOpsApp", "main"]

LOGGER = minimal_logger(__name__)
CONSOLE = Console()


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
        self._options: List[MenuOption] = [
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

        instructions = (
            "[bold]Enter a number[/bold] to launch a module, "
            "[bold]R[/bold] to run all, or [bold]Q[/bold] to exit."
        )
        return Panel(
            table,
            title="ShadowOps Persistent Shell",
            subtitle=instructions,
            border_style="magenta",
        )

    def _render_menu(self) -> None:
        self._console.print(self._menu_panel())

    # ------------------------------------------------------------------
    # Command dispatch
    # ------------------------------------------------------------------

    def _run_entry(self, option: MenuOption, *, pause: bool = True) -> bool:
        self._console.print(
            f"\n[bold green]► Launching[/bold green] {option.label}...", highlight=False
        )
        self._console.rule(f"[bold cyan]{option.label}[/bold cyan]", style="cyan")
        try:
            option.entry.handler()
        except Exception as exc:  # pragma: no cover - defensive guard for handlers
            LOGGER.error("Module '%s' raised an exception: %s", option.label, exc)
            self._console.print(
                f"[bold red]Module '{option.label}' failed:[/bold red] {exc}",
            )
        finally:
            self._console.rule(style="cyan")

        if not pause:
            return False

        return self._prompt_after_module()

    def _prompt_after_module(self) -> bool:
        prompt = Panel.fit(
            "[bold yellow]Press Enter to return to the main menu.[/bold yellow]\n"
            "[bold magenta]Type 'q' to quit the ShadowOps shell.[/bold magenta]",
            border_style="bright_black",
        )
        self._console.print(prompt)

        while True:
            response = (
                self._console.input("[bold yellow]Command[/bold yellow]: ")
                .strip()
                .lower()
            )
            if response in {"", "continue", "c"}:
                return False
            if response in {"q", "quit", "exit"}:
                return True
            self._console.print(
                "[bold red]Invalid response.[/bold red] Press Enter or type 'q' to quit."
            )

    def _run_all(self) -> None:
        self._console.print("\n[bold blue]Running all modules sequentially...[/bold blue]")
        for option in self._options:
            self._run_entry(option, pause=False)

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

            if self._run_entry(option):
                self._console.print("\n[bold magenta]Goodbye![/bold magenta]")
                return

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

        self._run_entry(option, pause=False)
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

    if argv is None:
        app_context = ShadowOpsApp()
    else:
        app_context = ShadowOpsApp(argv=list(argv))

    with app_context as app:
        try:
            app.run()
        except KeyboardInterrupt:  # pragma: no cover - interactive guard
            CONSOLE.print("\n[bold red]Interrupted by user.[/bold red]")
            return 130
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
