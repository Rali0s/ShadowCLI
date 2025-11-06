"""Audio synthesis helpers for the CLI lab."""

from __future__ import annotations

import math
import wave
from io import BytesIO
from pathlib import Path
from typing import Tuple

SAMPLE_RATE = 44100

try:  # optional playback
    import simpleaudio  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    simpleaudio = None  # type: ignore


def _render_waveform(frequencies: Tuple[float, ...], duration: float, volume: float) -> bytes:
    total_samples = int(SAMPLE_RATE * duration)
    frames = bytearray()
    for index in range(total_samples):
        sample_time = index / SAMPLE_RATE
        values = [math.sin(2.0 * math.pi * frequency * sample_time) for frequency in frequencies]
        value = sum(values) / max(1, len(values))
        amplitude = int(volume * 32767 * value)
        for _ in frequencies:
            frames.extend(int(amplitude).to_bytes(2, byteorder="little", signed=True))
    return bytes(frames)


def _write_wave(frames: bytes, channels: int, path: Path | None = None) -> Path | BytesIO:
    if path is None:
        buffer = BytesIO()
        with wave.open(buffer, "wb") as wav:
            wav.setnchannels(channels)
            wav.setsampwidth(2)
            wav.setframerate(SAMPLE_RATE)
            wav.writeframes(frames)
        buffer.seek(0)
        return buffer

    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(channels)
        wav.setsampwidth(2)
        wav.setframerate(SAMPLE_RATE)
        wav.writeframes(frames)
    return path


def generate_single_tone(frequency: float, duration: float, *, volume: float = 0.4, path: Path | None = None) -> Path | BytesIO:
    frames = _render_waveform((frequency,), duration, volume)
    return _write_wave(frames, 1, path)


def generate_binaural_tone(carrier: float, beat: float, duration: float, *, volume: float = 0.4, path: Path | None = None) -> Path | BytesIO:
    left = carrier - beat / 2
    right = carrier + beat / 2
    frames = _render_waveform((left, right), duration, volume)
    return _write_wave(frames, 2, path)


def play_audio(buffer: Path | BytesIO) -> None:
    if simpleaudio is None:
        print("Playback requires the optional 'simpleaudio' dependency. The WAV file has been generated instead.")
        return
    if isinstance(buffer, Path):
        wave_obj = simpleaudio.WaveObject.from_wave_file(str(buffer))
    else:
        buffer.seek(0)
        with wave.open(buffer, "rb") as wav:
            audio_data = wav.readframes(wav.getnframes())
            wave_obj = simpleaudio.WaveObject(
                audio_data,
                wav.getnchannels(),
                wav.getsampwidth(),
                wav.getframerate(),
            )
    play_obj = wave_obj.play()
    play_obj.wait_done()


def ensure_output_directory() -> Path:
    output = Path.home() / ".shadowops" / "cli" / "audio"
    output.mkdir(parents=True, exist_ok=True)
    return output
