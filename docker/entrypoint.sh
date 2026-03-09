#!/bin/sh
set -eu

PORT="${PORT:-8000}"

alembic upgrade head
exec uvicorn research_assistant_api.main:app --host 0.0.0.0 --port "${PORT}"
