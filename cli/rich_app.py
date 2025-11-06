"""Rich + Typer powered auxiliary CLI for ShadowOps."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

import typer
from rich import box
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree

from . import get_content_path
from .audio.generators import (
    generate_binaural_tone,
    generate_single_tone,
    play_audio,
)
from .audio.presets import FrequencyPreset, iter_presets
from .ncebg import launch_visual_neural_looper

__all__ = ["app"]

console = Console()

app = typer.Typer(
    name="ShadowOps Rich CLI",
    help="[bold]ShadowOps[/bold] auxiliary interface enhanced with Rich output and Typer commands.",
    no_args_is_help=True,
    rich_markup_mode="rich",
)

manuals_app = typer.Typer(
    help="Interact with the parsed manuals archive using rich formatting.",
    rich_markup_mode="rich",
)
app.add_typer(manuals_app, name="manuals")


# ---------------------------------------------------------------------------
# Manual utilities
# ---------------------------------------------------------------------------


def _manuals_root() -> Path:
    return get_content_path() / "manuals_data"


def _manual_dirs() -> Iterable[Path]:
    root = _manuals_root()
    if not root.exists():
        return []
    return sorted((path for path in root.iterdir() if path.is_dir()), key=lambda p: p.name.lower())


@manuals_app.command("list")
def list_manuals() -> None:
    """Display the manuals hierarchy using a Rich tree."""

    root = _manuals_root()
    if not root.is_dir():
        console.print(
            Panel(
                f"Manual data directory not found at [bold red]{root}[/bold red].",
                title="Manuals Unavailable",
                border_style="red",
            )
        )
        raise typer.Exit(code=1)

    tree = Tree("[bold cyan]manuals_data[/bold cyan]", guide_style="bold bright_black")
    for manual in _manual_dirs():
        manual_label = manual.name.replace("_", " ")
        manual_node = tree.add(f"[bold yellow]📚 {manual.name}[/bold yellow]  •  {manual_label}")
        for section in sorted(manual.glob("*.md"), key=lambda p: p.name.lower()):
            manual_node.add(f"[green]•[/green] {section.name}")

    console.print(
        Panel(
            tree,
            title="Project Manuals Index",
            border_style="blue",
            padding=(1, 2),
        )
    )
    console.print(
        "Use [bold green]shadowops-rich manuals read <manual> <section>[/bold green] to open a document.",
    )


@manuals_app.command("read")
def read_manual(
    manual_id: str = typer.Argument(..., help="Directory name of the manual, e.g. 01_SUN_STREAK."),
    section_file: str = typer.Argument(..., help="Markdown file name to open, e.g. 1.1_Overview.md."),
) -> None:
    """Render a manual section using Rich markdown."""

    root = _manuals_root()
    path = root / manual_id / section_file
    if not path.exists():
        console.print(
            Panel(
                f"Section [bold]{section_file}[/bold] not found within manual [bold]{manual_id}[/bold].\n"
                f"Looked for [italic]{path}[/italic].",
                title="Missing Section",
                border_style="red",
            )
        )
        raise typer.Exit(code=1)

    content = path.read_text(encoding="utf-8")
    title = manual_id.replace("_", " ")
    console.print(
        Panel(
            Markdown(content, code_theme="monokai", inline_code_lexer="markdown"),
            title=f"📖 {title} / {section_file}",
            border_style="green",
            padding=(1, 2),
            expand=True,
        )
    )


# ---------------------------------------------------------------------------
# Module overviews & presets
# ---------------------------------------------------------------------------


def _module_tree() -> Tree:
    tree = Tree("[bold white]ShadowOps Toolkit[/bold white]", guide_style="bright_black")
    ops = tree.add("[cyan]Operations Manual[/cyan]")
    ops.add("Plain-text viewer for the training operations primer.")

    research = tree.add("[cyan]Research Archive[/cyan]")
    research.add("Interactive retrieval of remote research dossiers.")

    audio_lab = tree.add("[cyan]Audio Frequency Lab[/cyan]")
    audio_lab.add("Design, preview, and export entrainment tones.")

    rv = tree.add("[cyan]Remote Viewing Training[/cyan]")
    rv.add("Session logger for practice targets and notes.")

    ncebg = tree.add("[cyan]NCNGB Experimental Modules[/cyan]")
    ncebg.add("Metatron Neuro Wheel visualizer and manuals explorer.")
    return tree


@app.command("modules")
def show_modules() -> None:
    """Display an overview tree of the available toolkit modules."""

    console.print(
        Panel(
            _module_tree(),
            title="Example Terminal CLI Interface",
            subtitle="Launch modules via the classic menu or the Typer commands shown here.",
            border_style="magenta",
            padding=(1, 2),
        )
    )


def _build_preset_table(presets: Iterable[FrequencyPreset]) -> Table:
    table = Table(box=box.SIMPLE_HEAVY, expand=True)
    table.add_column("Preset", style="bold yellow")
    table.add_column("Carrier", justify="right")
    table.add_column("Beat", justify="right")
    table.add_column("Description")
    for preset in presets:
        beat = f"{preset.beat_hz:.1f} Hz" if preset.beat_hz else "—"
        table.add_row(preset.name, f"{preset.carrier_hz:.1f} Hz", beat, preset.description)
    return table


@app.command("presets")
def list_presets() -> None:
    """Show the catalogue of audio lab frequency presets."""

    console.print(
        Panel(
            _build_preset_table(iter_presets()),
            title="Audio Frequency Presets",
            border_style="cyan",
            padding=(1, 1),
        )
    )


# ---------------------------------------------------------------------------
# Neuro sync integration
# ---------------------------------------------------------------------------


@dataclass
class SyncConfiguration:
    label: str
    carrier_hz: float
    beat_hz: float
    duration: float
    volume: float

    @property
    def pulse_hz(self) -> float:
        return self.beat_hz if self.beat_hz > 0 else self.carrier_hz


def _resolve_preset(name: str) -> Optional[FrequencyPreset]:
    needle = name.strip().lower()
    for preset in iter_presets():
        if preset.name.lower() == needle:
            return preset
    return None


def _render_sync_summary(config: SyncConfiguration) -> None:
    grid = Table.grid(padding=(0, 1))
    grid.add_column(justify="right", style="bold")
    grid.add_column()
    grid.add_row("Mode", config.label)
    grid.add_row("Carrier", f"{config.carrier_hz:.2f} Hz")
    beat_label = f"{config.beat_hz:.2f} Hz" if config.beat_hz > 0 else "Single tone"
    grid.add_row("Beat", beat_label)
    grid.add_row("Duration", f"{config.duration:.0f} seconds")
    grid.add_row("Volume", f"{config.volume:.2f}")
    console.print(
        Panel(
            grid,
            title="Neuro Synchronisation",
            border_style="bright_magenta",
            padding=(1, 1),
        )
    )


@app.command("neuro-sync")
def neuro_sync(
    preset: Optional[str] = typer.Option(
        None,
        "--preset",
        "-p",
        help="Name of an audio lab preset to load (e.g. 'Alpha Flow State').",
    ),
    carrier: Optional[float] = typer.Option(
        None,
        "--carrier",
        min=20.0,
        help="Carrier frequency in Hz when not using a preset.",
    ),
    beat: Optional[float] = typer.Option(
        None,
        "--beat",
        min=0.0,
        help="Binaural beat offset in Hz (0 for single tone).",
    ),
    duration: float = typer.Option(180.0, min=10.0, help="Tone duration in seconds."),
    volume: float = typer.Option(0.35, min=0.05, max=1.0, help="Playback volume scale."),
    scene_seconds: Optional[float] = typer.Option(
        None,
        help="Automatically close the visualiser after this many seconds. Defaults to the tone duration.",
    ),
    visual: bool = typer.Option(
        True,
        "--visual/--no-visual",
        help="Launch the Metatron Neuro Wheel visualiser alongside the audio.",
    ),
) -> None:
    """Launch the audio lab tone generator in sync with the NCNGB visual module."""

    preset_obj: Optional[FrequencyPreset] = None
    if preset:
        preset_obj = _resolve_preset(preset)
        if not preset_obj:
            console.print(
                Panel(
                    f"Preset [bold]{preset}[/bold] was not found. Use [green]shadowops-rich presets[/green] to list options.",
                    title="Unknown Preset",
                    border_style="red",
                )
            )
            raise typer.Exit(code=1)
        carrier_hz = preset_obj.carrier_hz
        beat_hz = preset_obj.beat_hz or 0.0
        label = preset_obj.name
    else:
        if carrier is None:
            console.print(
                Panel(
                    "Provide either a preset name or a carrier frequency.",
                    title="Missing configuration",
                    border_style="red",
                )
            )
            raise typer.Exit(code=1)
        carrier_hz = carrier
        beat_hz = beat or 0.0
        label = "Custom"

    config = SyncConfiguration(label=label, carrier_hz=carrier_hz, beat_hz=beat_hz, duration=duration, volume=volume)
    _render_sync_summary(config)

    console.print("[bold cyan]Rendering tone buffer…[/bold cyan]")
    try:
        buffer = (
            generate_binaural_tone(config.carrier_hz, config.beat_hz, config.duration, volume=config.volume)
            if config.beat_hz > 0
            else generate_single_tone(config.carrier_hz, config.duration, volume=config.volume)
        )
    except Exception as exc:  # pragma: no cover - synthesis errors are unexpected
        console.print(Panel(f"Audio generation failed: {exc}", border_style="red"))
        raise typer.Exit(code=1) from exc

    process: Optional[subprocess.Popen[bytes]] = None
    if visual:
        console.print("[bold cyan]Launching Metatron Neuro Wheel…[/bold cyan]")
        process = launch_visual_neural_looper(
            pulse_hz=config.pulse_hz,
            scene_seconds=scene_seconds or config.duration,
            wait=False,
        )
        if process is None:
            console.print(
                Panel(
                    "Visual module could not be started. Verify that [italic]pygame[/italic] is installed.",
                    title="Visualiser unavailable",
                    border_style="yellow",
                )
            )
        else:
            console.print("Visualiser started in a separate window. Use ESC to exit.")

    console.print("[bold green]Playing audio…[/bold green]")
    try:
        play_audio(buffer)
    except KeyboardInterrupt:  # pragma: no cover - interactive cancellation
        console.print("\nPlayback interrupted by user.")
    finally:
        if process is not None:
            timeout = scene_seconds or config.duration
            if timeout > 0:
                try:
                    process.wait(timeout=timeout + 2)
                except subprocess.TimeoutExpired:
                    console.print("Visualiser is still running; close the window to finish.")

    console.print(Panel("Session complete.", border_style="green"))


if __name__ == "__main__":  # pragma: no cover
    app()
