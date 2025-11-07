# ShadowCLI
ShadowOps-PyCLI

## Rich Typer Add-on

Install the optional [Typer](https://typer.tiangolo.com/) + [Rich](https://rich.readthedocs.io/) interface and invoke it with:

```bash
pip install -e .
shadowops-rich --help
```

## Rich Persistent Shell

Prefer a classic looping menu? The Rich-powered shell now combines Rich with
[`simple-term-menu`](https://github.com/IngoMeyer441/simple-term-menu) so you
can navigate with the arrow keys while the menu remains on screen:

```bash
pip install -e .
shadowops-rich shell          # launches the interactive loop
shadowops-rich shell --list   # show modules without entering the loop
shadowops-rich shell --module 2
shadowops-rich shell --run-all
```

Use `--module` with either a number or a module name to jump directly into a
tool, or `--run-all` to execute each module sequentially. Press `q` at any
time while the menu is focused to exit instantly.

### Manual navigation

```bash
shadowops-rich manuals list
shadowops-rich manuals read 01_SUN_STREAK 1.1_Overview.md
```

### Module overview

```bash
shadowops-rich modules
```

### Audio / Visual Neuro Sync

Launch the Metatron Neuro Wheel visualiser in sync with an entrainment tone:

```bash
shadowops-rich neuro-sync --preset "Alpha Flow State" --duration 120
```

Use `--no-visual` to preview only the audio, or `--carrier`/`--beat` for custom configurations. The visualiser will automatically close after the tone finishes when the optional `pygame` dependency is available.
