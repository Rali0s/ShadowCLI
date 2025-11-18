"""NCNGB experimental modules integration."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from .. import get_content_path
from ..menu import Menu, MenuItem

__all__ = ["run", "show_manual_tree", "launch_visual_neural_looper"]


def _manual_tree_lines(root: Path) -> list[str]:
    entries = sorted(root.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
    lines: list[str] = []
    last_index = len(entries) - 1
    for index, entry in enumerate(entries):
        connector = "└── " if index == last_index else "├── "
        suffix = "/" if entry.is_dir() else ""
        lines.append(f"{connector}{entry.name}{suffix}")
        if entry.is_dir():
            extension = "    " if index == last_index else "│   "
            for child in _manual_tree_lines(entry):
                lines.append(f"{extension}{child}")
    return lines


def show_manual_tree() -> None:
    """Print the manuals_data directory as an ASCII tree."""

    manuals_root = get_content_path() / "manuals_data"
    if not manuals_root.exists():
        print(f"Manual data directory not found: {manuals_root}")
        return

    print("\nManual Section Tree\n")
    print(f"{manuals_root.name}/")
    for line in _manual_tree_lines(manuals_root):
        print(line)
    print()


def launch_visual_neural_looper(
    *,
    pulse_hz: float | None = None,
    speed_trim: float | None = None,
    scene_seconds: float | None = None,
    wait: bool = True,
) -> subprocess.Popen[bytes] | None:
    """Run the Metatron visual neural looper in a subprocess.

    Parameters
    ----------
    pulse_hz:
        Optional override for the central pulse frequency.
    speed_trim:
        Optional override for animation speed multiplier.
    scene_seconds:
        Auto-exit duration for the visualiser. ``None`` keeps the default runtime.
    wait:
        When ``True`` (default) blocks until the subprocess exits. When ``False``
        returns the :class:`subprocess.Popen` handle for asynchronous control.
    """

    try:
        __import__("pygame")
    except ModuleNotFoundError:
        print("The visual neural looper requires the 'pygame' package to be installed.")
        print("Install it with 'pip install pygame' and try again.")
        return None

    script_path = Path(__file__).with_name("metatron_neuro_wheel_fluid.py")
    if not script_path.exists():
        print(f"Visual neural looper script not found: {script_path}")
        return None

    print("Launching the Metatron Neuro Wheel visualizer...\n")
    args = [sys.executable, str(script_path)]
    if pulse_hz is not None:
        args.extend(["--pulse-hz", str(pulse_hz)])
    if speed_trim is not None:
        args.extend(["--speed-trim", str(speed_trim)])
    if scene_seconds is not None:
        args.extend(["--scene-seconds", str(scene_seconds)])
    try:
        if wait:
            subprocess.run(args, check=True)
            return None
        return subprocess.Popen(args)
    except subprocess.CalledProcessError as exc:
        print("The visualizer exited with an error.")
        print(f"Return code: {exc.returncode}")
    return None


def run() -> None:
    """Entry point for NCNGB integrations."""

    menu = Menu(
        "NCNGB Experimental Modules",
        [
            MenuItem("Manual Section Tree", show_manual_tree),
            MenuItem("Visual Neural Looper", launch_visual_neural_looper),
        ],
        exit_label="Back",
    )
    menu.show()
