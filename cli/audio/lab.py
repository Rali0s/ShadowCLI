"""Audio frequency lab CLI."""

from __future__ import annotations

import time
from datetime import datetime

from ..menu import Menu, MenuItem
from ..utils.text import format_table
from .generators import (
    ensure_output_directory,
    generate_binaural_tone,
    generate_single_tone,
    play_audio,
)
from .presets import FrequencyPreset, iter_presets


def _list_presets() -> None:
    rows = [
        (preset.name, f"{preset.carrier_hz} Hz", f"{preset.beat_hz or '—'} Hz", preset.description)
        for preset in iter_presets()
    ]
    print(format_table([("Name", "Carrier", "Beat", "Description")] + rows))


def _select_preset() -> FrequencyPreset | None:
    presets = list(iter_presets())
    from ..menu import TerminalMenu

    if TerminalMenu is not None:
        menu = TerminalMenu([preset.name for preset in presets], title="Choose preset\n")
        index = menu.show()
        if index is None:
            return None
        return presets[int(index)]
    for idx, preset in enumerate(presets, start=1):
        print(f"{idx}. {preset.name}")
    raw = input("Select preset: ").strip()
    if not raw:
        return None
    try:
        return presets[int(raw) - 1]
    except Exception:
        return None


def _prompt_float(prompt: str, default: float) -> float:
    raw = input(f"{prompt} [{default}]: ").strip()
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        print("Invalid number, using default value.")
        return default


def _render_visual(frequency: float, duration: float = 5.0) -> None:
    print(f"Visualising frequency {frequency:.2f} Hz for {duration} seconds...")
    frames = ["▁", "▂", "▃", "▄", "▅", "▆", "▇", "█", "▇", "▆", "▅", "▄", "▃", "▂"]
    step_time = max(0.05, min(0.25, 1.0 / max(frequency, 1.0)))
    end_time = time.time() + duration
    index = 0
    while time.time() < end_time:
        print("\r" + frames[index % len(frames)] * 40, end="", flush=True)
        index += 1
        time.sleep(step_time)
    print("\r" + " " * 40 + "\rVisualisation complete.\n")


def _play_preset() -> None:
    preset = _select_preset()
    if preset is None:
        return
    duration = _prompt_float("Duration (seconds)", 300.0 if preset.beat_hz else 120.0)
    volume = _prompt_float("Volume (0.0 – 1.0)", 0.4)
    output_dir = ensure_output_directory()
    filename = f"{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}-{preset.name.replace(' ', '-').lower()}.wav"
    path = output_dir / filename
    if preset.beat_hz:
        buffer = generate_binaural_tone(preset.carrier_hz, preset.beat_hz, duration, volume=volume, path=path)
    else:
        buffer = generate_single_tone(preset.carrier_hz, duration, volume=volume, path=path)
    print(f"WAV file saved to {path}")
    play_audio(buffer)


def _custom_tone() -> None:
    frequency = _prompt_float("Carrier frequency (Hz)", 220.0)
    beat = _prompt_float("Binaural beat (Hz, 0 for single tone)", 0.0)
    duration = _prompt_float("Duration (seconds)", 180.0)
    volume = _prompt_float("Volume (0.0 – 1.0)", 0.4)
    output_dir = ensure_output_directory()
    filename = f"custom-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}.wav"
    path = output_dir / filename
    if beat > 0:
        buffer = generate_binaural_tone(frequency, beat, duration, volume=volume, path=path)
    else:
        buffer = generate_single_tone(frequency, duration, volume=volume, path=path)
    print(f"WAV file saved to {path}")
    play_audio(buffer)


def run() -> None:
    actions = [
        MenuItem("List frequency presets", _list_presets),
        MenuItem("Play preset", _play_preset),
        MenuItem("Design custom tone", _custom_tone),
        MenuItem("Visualise frequency", lambda: _render_visual(_prompt_float("Frequency (Hz)", 8.0))),
    ]
    menu = Menu("Audio Frequency Lab", actions)
    menu.show()
