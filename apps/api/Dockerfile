FROM python:3.13-slim
WORKDIR /app
ENV UV_PROJECT_ENVIRONMENT=/app/.venv PATH="/app/.venv/bin:$PATH" PYTHONDONTWRITEBYTECODE=1
ARG BUILD_CA
RUN --mount=type=secret,id=build_ca,target=/run/secrets/build_ca PIP_CERT="${BUILD_CA:-/etc/ssl/certs/ca-certificates.crt}" pip install --no-cache-dir uv==0.13.6
COPY pyproject.toml uv.lock ./
RUN --mount=type=secret,id=build_ca,target=/run/secrets/build_ca SSL_CERT_FILE="${BUILD_CA:-/etc/ssl/certs/ca-certificates.crt}" uv sync --frozen --no-dev --no-install-project
COPY apps/api ./apps/api
COPY apps/__init__.py ./apps/
COPY libs ./libs
COPY services ./services
COPY migrations ./migrations
COPY alembic.ini ./
RUN chmod -R a+rX apps libs services migrations pyproject.toml alembic.ini
USER 10001:10001
CMD ["uvicorn","apps.api.main:create_app","--factory","--host","0.0.0.0","--port","8000"]
