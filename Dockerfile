FROM python:3.12-slim-bookworm

# avoid needing pip
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1

COPY pyproject.toml /app/
COPY uv.lock /app/

# for caching
RUN uv sync --no-dev --no-install-project

COPY . /app

RUN uv sync --no-dev

ENV PATH="/app/.venv/bin:$PATH"

# change this to specifc function in scripts/pyproject.toml
CMD ["uv","run","prod"]
