"""Check module registry — discovers and returns check instances."""

from __future__ import annotations

from typing import List, Optional

from andio.checks.base import BaseCheck

# Registry of all check classes. Each check module appends to this on import.
_REGISTRY: List[type] = []
_LOADED = False


def register(cls: type) -> type:
    """Class decorator to register a check."""
    if cls not in _REGISTRY:
        _REGISTRY.append(cls)
    return cls


def _ensure_loaded():
    """Import all check modules so they register themselves."""
    global _LOADED
    if _LOADED:
        return
    _LOADED = True
    from andio.checks import focusable  # noqa: F401
    from andio.checks import global_checks  # noqa: F401
    from andio.checks import graphics  # noqa: F401
    from andio.checks import hidden  # noqa: F401
    from andio.checks import links  # noqa: F401
    from andio.checks import structures  # noqa: F401


def get_checks(
    names: Optional[List[str]] = None,
    version: str = "v1",
) -> List[BaseCheck]:
    """Return instantiated checks, filtered by name and version.

    Args:
        names: If provided, only return checks whose id is in this list.
        version: Only return checks matching this version.
    """
    _ensure_loaded()
    checks = []
    for cls in _REGISTRY:
        instance = cls()
        if instance.version != version:
            continue
        if names is not None and instance.id not in names:
            continue
        checks.append(instance)
    return checks
