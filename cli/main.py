"""Command line entry point for ShadowOps offline toolkit."""

from __future__ import annotations

from .menu import Menu, MenuItem
from .navigation import ENTRIES


def run_all() -> None:
    for entry in ENTRIES:
        print(f"\n=== {entry.label.upper()} ===\n")
        entry.handler()


def main() -> None:
    actions = [MenuItem(entry.label, entry.handler) for entry in ENTRIES]
    actions.insert(0, MenuItem("Run all modules", run_all))
    menu = Menu("ShadowOps Offline Toolkit", actions)
    menu.show()


if __name__ == "__main__":  # pragma: no cover
    main()
