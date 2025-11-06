"""Frequency presets used by the audio lab."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class FrequencyPreset:
    name: str
    description: str
    carrier_hz: float
    beat_hz: float | None = None


PRESETS: tuple[FrequencyPreset, ...] = (
    FrequencyPreset("Delta Deep Calm", "Grounding and recovery", carrier_hz=120, beat_hz=2.5),
    FrequencyPreset("Theta Memory Weave", "Hypnagogic rehearsal and imagery", carrier_hz=180, beat_hz=6.0),
    FrequencyPreset("Alpha Flow State", "Focused studying and relaxed alertness", carrier_hz=220, beat_hz=10.0),
    FrequencyPreset("Beta Activation", "Task execution and rapid recall", carrier_hz=340, beat_hz=18.0),
    FrequencyPreset("Gamma Burst", "High-integration synthesis", carrier_hz=480, beat_hz=40.0),
)


def iter_presets() -> Iterable[FrequencyPreset]:
    return PRESETS
