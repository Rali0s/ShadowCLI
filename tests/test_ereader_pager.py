import sys
import termios
import tty
import shutil
import os
from pathlib import Path

import pytest

import cli.ereader as ereader


class MockStdin:
    def __init__(self, inputs):
        self._inputs = list(inputs)

    def fileno(self):
        return 0

    def read(self, n=1):
        if not self._inputs:
            return ""
        return self._inputs.pop(0)


def test_ansi_inprocess_pager_quit(tmp_path, monkeypatch):
    md = tmp_path / "sample.md"
    md.write_text("# Test\n\nThis is a simple test of the ANSI pager.\nLine 3\nLine 4\n")

    # Make terminal size predictable
    monkeypatch.setattr(shutil, "get_terminal_size", lambda default=(80, 24): os.terminal_size((40, 10)))

    # Stub out termios/tty operations used by the pager
    monkeypatch.setattr(termios, "tcgetattr", lambda fd: [0])
    monkeypatch.setattr(termios, "tcsetattr", lambda fd, when, attr: None)
    monkeypatch.setattr(tty, "setcbreak", lambda fd: None)

    # Replace stdin with a mock that sends 'q' immediately to quit
    monkeypatch.setattr(sys, "stdin", MockStdin(["q"]))

    # Run the pager - it should return without raising
    ereader._ansi_inprocess_pager(md)

    # If we reached here, the pager loop handled the quit key successfully.
    assert True
