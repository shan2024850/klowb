"""Request-scoped access to application singletons.

Everything the routers need lives on ``app.state.container`` (set in
``apps.api.main``), so tests can build an app with substitutes.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Request

from apps.api.settings import Settings
from libs.domain.clock import Clock
from libs.observability.metrics import Metrics
from libs.storage.cache import Cache
from libs.storage.database import Database


@dataclass(frozen=True, slots=True)
class Container:
    settings: Settings
    clock: Clock
    metrics: Metrics
    database: Database
    cache: Cache | None


def get_container(request: Request) -> Container:
    container: Container = request.app.state.container
    return container


ContainerDep = Annotated[Container, Depends(get_container)]
