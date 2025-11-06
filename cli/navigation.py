"""Navigation configuration for the CLI."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .audio import lab as audio_lab
from .operations import run as ops_manual
from .research import archive as research_archive
from .rv import cli as rv_cli


@dataclass(frozen=True)
class NavigationEntry:
    label: str
    handler: Callable[[], None]


ENTRIES: tuple[NavigationEntry, ...] = (
    NavigationEntry("Operations Manual", ops_manual),
    NavigationEntry("Research Archive", research_archive.run),
    NavigationEntry("Audio Frequency Lab", audio_lab.run),
    NavigationEntry("Remote Viewing Training", rv_cli.run),
)
