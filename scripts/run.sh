#!/usr/bin/env sh
set -e

ENV="local"
if [ $# -gt 0 ]; then
  case "$1" in
    local|stage|staging|prod|production)
      ENV="$1"
      shift
      ;;
  esac
fi

COMPOSE_FILES="-f docker-compose.yml"

case "$ENV" in
  local)
    ;;
  stage|staging)
    if [ -f docker-compose.stage.yml ]; then
      COMPOSE_FILES="$COMPOSE_FILES -f docker-compose.stage.yml"
    else
      echo "Missing docker-compose.stage.yml" >&2
      exit 1
    fi
    ;;
  prod|production)
    if [ -f docker-compose.prod.yml ]; then
      COMPOSE_FILES="$COMPOSE_FILES -f docker-compose.prod.yml"
    else
      echo "Missing docker-compose.prod.yml" >&2
      exit 1
    fi
    ;;
  *)
    echo "Usage: $0 [local|stage|prod] [docker compose args...]" >&2
    exit 1
    ;;
 esac

docker compose $COMPOSE_FILES up --build "$@"
