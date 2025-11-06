"""ShadowOps command line interface package."""

from pathlib import Path

__all__ = ["get_content_path"]


def get_content_path() -> Path:
    """Return the root directory that stores shared Markdown content."""
    return Path(__file__).resolve().parent.parent / "content"
