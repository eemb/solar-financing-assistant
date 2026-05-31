"""Session-wide pytest configuration.

The lru_cache singletons in dependencies.py are global; without clearing them
they persist across the full test suite and cause state leakage through the
shared InMemorySimulationRepository.  The autouse fixture below tears them
down after every test so each test starts from a clean slate.
"""

from __future__ import annotations

import pytest

from solar_financing_assistant.interface.api.dependencies import (
    _cached_settings,
    _cached_tools,
)


@pytest.fixture(autouse=True)
def _clear_dependency_caches() -> None:  # type: ignore[return]
    yield
    _cached_settings.cache_clear()
    _cached_tools.cache_clear()
