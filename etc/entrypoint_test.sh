#!/usr/bin/env sh
set -e

alembic upgrade head
pytest app/tests/ --cov=.