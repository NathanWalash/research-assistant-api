FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app/src

WORKDIR /app

COPY pyproject.toml pyproject.toml
COPY README.md README.md
COPY src src

RUN python -m pip install --upgrade pip \
    && python -m pip install .

COPY alembic alembic
COPY alembic.ini alembic.ini
COPY docker docker

RUN chmod +x docker/entrypoint.sh

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 CMD python -c "from urllib.request import urlopen; urlopen('http://127.0.0.1:8000/health')"

CMD ["./docker/entrypoint.sh"]
