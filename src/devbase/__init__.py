"""DevBase - Personal Engineering Operating System."""

try:
    from importlib.metadata import version, PackageNotFoundError
except ImportError:
    from importlib_metadata import version, PackageNotFoundError  # type: ignore

try:
    __version__ = version("devbase")
except PackageNotFoundError:
    __version__ = "5.1.0-alpha.1"  # Fallback for local dev without install
