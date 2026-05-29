"""Backward-compatible re-export of application settings.

The canonical settings module is ``solar_financing_assistant.config.settings``.
This module re-exports ``Settings``, ``settings``, and ``configure_logging``
so that existing imports from ``infrastructure.config`` continue to work.
"""

from solar_financing_assistant.config.settings import (  # noqa: F401
    Settings,
    configure_logging,
    settings,
)
