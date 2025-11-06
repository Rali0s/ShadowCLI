"""Input/output helpers for CLI flows."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def prompt_multiline(prompt: str) -> list[str]:
    print(prompt)
    print("Enter a blank line to finish.")
    responses: list[str] = []
    while True:
        line = input("» ").rstrip()
        if not line:
            break
        responses.append(line)
    return responses


def ensure_directory(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def dump_json(path: Path, payload: Any) -> None:
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
