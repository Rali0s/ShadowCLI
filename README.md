# ShadowCLI
ShadowOps PyCLI — interactive command-line toolkit with Rich UI and a Cement-powered shell.

## Quick start

Install editable (recommended for development):

```bash
pip install -e .
```

There are two primary entry points:

- Rich/Typer interface (feature-rich, colored): `shadowops-rich --help`
- Cement persistent shell (menu-driven): `shadowops-cement`

Example:

```bash
shadowops-cement          # launches the interactive loop
shadowops-cement --list   # show modules without entering the loop
shadowops-cement --module 2
```

## Manuals Browser and Reader Modes

We provide an integrated manuals browser that keeps manual content inside the shell frame (no long scrollback). Key features:

- In-panel manual viewer (used by both the Cement shell and the Research Archive).
- Two reader modes: `ansi` (Rich-colored Markdown) and `curses` (original curses pager).
- Auto-resize and reflow on terminal resize (SIGWINCH).
- Help overlay while reading: press `h` to toggle a short key help.
- Safe ANSI decoding so colored output renders correctly inside Rich Panels.

Commands / usage

```bash
shadowops-rich manuals list
shadowops-rich manuals read <manual_section> <file.md> [--reader-mode ansi|curses]
```

Reader selection order

1. `--reader-mode` command-line flag (explicit choice)
2. `E_READER_MODE` environment variable (`ansi` or `curses`)
3. Automatic detection (TTY + capabilities)

Force ANSI rendering even when curses might be available:

```bash
E_READER_FORCE_ANSI=1 shadowops-rich manuals read 01_SUN_STREAK 1.1_Overview.md
```

Navigation inside the in-panel reader

- j / k: scroll line-by-line
- SPACE: page-down
- b: page-up
- gg: go to top (press g twice)
- G: go to bottom
- /: search (enter query)
- h: toggle help overlay
- q: quit back to menu

## Research Archive

Selecting a document in the Research Archive opens it inside the same panel viewer (no external pager). The viewer renders the document's title and metadata followed by content.

## Audio / Visual Neuro Sync

Launch the Metatron Neuro Wheel visualiser in sync with an entrainment tone:

```bash
shadowops-rich neuro-sync --preset "Alpha Flow State" --duration 120
```

New visualiser flags

- `--scale-up` — allow the visualiser to upscale for large displays
- `--no-scale-font` — do not scale fonts with visuals
- `--fill-factor <0.1-1.0>` — control how much of the window the wheel occupies
- `--fullscreen` — request fullscreen mode

If the optional `pygame` dependency is missing the visualiser will gracefully fall back and print instructions for installation.

## Notes and troubleshooting

- If you see import errors about `get_content_path`, try running commands as a module (e.g., `python -m cli.main`) or ensure the package is installed in editable mode (`pip install -e .`). The code includes robust fallbacks for different invocation styles.
- If a manual doesn't render as expected, try forcing `ansi` mode or resizing your terminal to trigger reflow.

## Contributing

Contributions welcome — please open PRs or issues on the repository. For development, run the import checks and unit tests that exercise the ereader/pager components.
