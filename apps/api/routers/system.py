"""System information for the UI: mode, version, feed-quality legend. No secrets."""

from __future__ import annotations

from fastapi import APIRouter

from apps.api.deps import ContainerDep
from libs.schemas.system import DISCLAIMER, FEED_QUALITY_LEGEND, SystemInfo

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/info", response_model=SystemInfo, summary="Build, trading mode and data legend.")
async def system_info(container: ContainerDep) -> SystemInfo:
    settings = container.settings
    return SystemInfo(
        name=settings.app_name,
        version=settings.app_version,
        environment=settings.app_env,
        trading_mode=settings.trading_mode,
        live_trading_available=settings.live_trading_available,
        llm_enabled=settings.llm_enabled,
        server_time=container.clock.now(),
        feed_quality_legend=list(FEED_QUALITY_LEGEND),
        disclaimer=DISCLAIMER,
    )
