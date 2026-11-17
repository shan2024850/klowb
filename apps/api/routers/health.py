"""Liveness, readiness and metrics endpoints (unversioned, for orchestrators)."""

from __future__ import annotations

from fastapi import APIRouter, Response
from fastapi.responses import JSONResponse

from apps.api.deps import ContainerDep
from apps.api.health import readiness
from libs.domain.enums import ReadinessStatus
from libs.schemas.system import ErrorEnvelope, LivenessReport, ReadinessReport

router = APIRouter(tags=["health"])


@router.get(
    "/healthz",
    response_model=LivenessReport,
    summary="Liveness: the process is running. Touches no dependency.",
)
async def healthz() -> LivenessReport:
    return LivenessReport()


@router.get(
    "/readyz",
    response_model=ReadinessReport,
    responses={503: {"model": ReadinessReport, "description": "A required dependency is down."}},
    summary="Readiness: dependency status. 503 when a required dependency is down.",
)
async def readyz(container: ContainerDep) -> JSONResponse:
    report = await readiness(
        database=container.database,
        cache=container.cache,
        clock=container.clock,
        metrics=container.metrics,
        timeout_seconds=container.settings.dependency_check_timeout_seconds,
    )
    status_code = 503 if report.status is ReadinessStatus.UNAVAILABLE else 200
    return JSONResponse(status_code=status_code, content=report.model_dump(mode="json"))


@router.get(
    "/metrics",
    summary="Prometheus metrics.",
    response_class=Response,
    responses={500: {"model": ErrorEnvelope}},
)
async def metrics(container: ContainerDep) -> Response:
    payload, content_type = container.metrics.render()
    return Response(content=payload, media_type=content_type)
