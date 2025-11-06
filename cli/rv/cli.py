"""Remote viewing training CLI."""

from __future__ import annotations

from pathlib import Path
from random import choice
from typing import List

from ..data.rv_targets import RvDifficulty, choose_target, filter_targets
from ..menu import Menu, MenuItem
from ..utils.io import ensure_directory, load_json
from ..utils.text import format_table
from .session import RvSession

STORAGE = ensure_directory(Path.home() / ".shadowops" / "cli")


def _choose_difficulty() -> RvDifficulty | None:
    options: List[RvDifficulty] = ["novice", "intermediate", "advanced"]
    from ..menu import TerminalMenu

    if TerminalMenu is not None:
        menu = TerminalMenu([opt.title() for opt in options] + ["Random"], title="Select difficulty\n")
        index = menu.show()
        if index is None:
            return None
        if index == len(options):
            return choice(options)
        return options[int(index)]
    for idx, label in enumerate(options, start=1):
        print(f"{idx}. {label.title()}")
    print(f"{len(options) + 1}. Random")
    raw = input("Choose difficulty: ").strip()
    if not raw:
        return None
    try:
        value = int(raw)
    except ValueError:
        return None
    if value == len(options) + 1:
        return choice(options)
    if 1 <= value <= len(options):
        return options[value - 1]
    return None


def _start_session() -> None:
    difficulty = _choose_difficulty()
    target = choose_target(difficulty=difficulty)
    session = RvSession(target)
    print(f"\nTarget assigned — difficulty: {target.difficulty.upper()}. Stage prompts will guide your data capture.\n")
    for idx in range(len(session.perceptions)):
        session.record(idx)
    record = session.complete(STORAGE)
    print("\nSession complete!\n")
    print(f"Target: {record.target_name} ({record.target_id})")
    print(f"Accuracy: {record.accuracy}%")
    if record.matches:
        print("Matched elements: " + ", ".join(record.matches))
    else:
        print("No direct element matches this time — review perceptions and repeat training.")


def _list_targets() -> None:
    rows = [
        (
            target.name,
            target.target_id,
            target.category.title(),
            target.difficulty.title(),
            ", ".join(target.correct_elements),
        )
        for target in filter_targets()
    ]
    print(format_table([("Name", "ID", "Category", "Difficulty", "Elements")] + rows))


def _history() -> None:
    history = load_json(STORAGE / "rv-history.json", default={"sessions": []})
    sessions = history.get("sessions", [])
    if not sessions:
        print("No sessions recorded yet. Complete a run to build history.\n")
        return
    rows = [
        (
            item["target_name"],
            item["target_id"],
            f"{item['accuracy']}%",
            item["completed_at"].split("T")[0],
        )
        for item in sessions
    ]
    print(format_table([("Target", "ID", "Accuracy", "Date")] + rows))


def run() -> None:
    actions = [
        MenuItem("Start training session", _start_session),
        MenuItem("List available targets", _list_targets),
        MenuItem("Review history", _history),
    ]
    menu = Menu("Remote Viewing Training", actions)
    menu.show()
