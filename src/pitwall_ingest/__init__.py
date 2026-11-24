"""Pitwall ingest: the starting point for every Pit Wall Python service."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("pitwall-ingest")
except PackageNotFoundError:  # pragma: no cover - only when running from an uninstalled checkout
    __version__ = "0.0.0"

__all__ = ["__version__"]
