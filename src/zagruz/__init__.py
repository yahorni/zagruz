import sys
from importlib.metadata import version

# PyInstaller workaround (no metadata in frozen builds)
if getattr(sys, 'frozen', False):
    from ._version import __version__
else:
    __version__ = version("zagruz")

__all__ = ["main"]


def __getattr__(name):
    if name == "main":
        # Lazy import to avoid circular dependency
        from .zagruz import main
        return main
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
