"""Terminal menu helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable, List, Optional

try:
    from simple_term_menu import TerminalMenu
except Exception:  # pragma: no cover - runtime guard if dependency missing
    TerminalMenu = None  # type: ignore


SelectionHandler = Callable[[], None]


@dataclass
class MenuItem:
    """Represents an actionable menu item."""

    label: str
    handler: SelectionHandler


class Menu:
    """Wrapper around :class:`simple_term_menu.TerminalMenu` with fallback logic."""

    def __init__(self, title: str, items: Iterable[MenuItem], exit_label: str = "Exit") -> None:
        self.title = title
        self.items: List[MenuItem] = list(items)
        self.exit_label = exit_label

    def show(self) -> None:
        while True:
            options = [item.label for item in self.items] + [self.exit_label]
            index = self._prompt(options)
            if index is None or index == len(options) - 1:
                return
            self.items[index].handler()

    def _prompt(self, options: List[str]) -> Optional[int]:
        if TerminalMenu is None:
            return self._fallback_prompt(options)

        menu = TerminalMenu(options, title=self.title + "\n")
        selected_index = menu.show()
        if selected_index is None:
            return None
        return int(selected_index)

    def _fallback_prompt(self, options: List[str]) -> Optional[int]:
        # Prefer a Rich-rendered prompt when available for a nicer fallback UI.
        try:
            from .rich_menu import choice

            selected = choice(options, title=self.title, footer="(blank to exit)")
            return selected
        except Exception:
            # Fall back to the simple text prompt if Rich isn't available or an error occurs.
            print(self.title)
            for idx, option in enumerate(options, start=1):
                print(f"{idx}. {option}")
            raw = input("Select an option (blank to exit): ").strip()
            if not raw:
                return None
            try:
                value = int(raw)
            except ValueError:
                print("Invalid selection. Please enter a number.")
                return None
            if value < 1 or value > len(options):
                print("Selection out of range.")
                return None
            return value - 1
