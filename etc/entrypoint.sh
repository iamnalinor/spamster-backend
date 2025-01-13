#!/usr/bin/env sh
set -e

alembic upgrade head
python3 -m uvicorn app:app --host=0.0.0.0 --port=8080