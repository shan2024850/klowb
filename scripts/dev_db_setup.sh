#!/usr/bin/env bash
# Create the local development/test PostgreSQL role and databases.
#
# DEVELOPMENT ONLY: the role uses a well-known password. Production must supply
# its own DATABASE_URL (the application refuses the dev default when APP_ENV=prod).
#
# Usage: scripts/dev_db_setup.sh        (needs a local PostgreSQL superuser `postgres`)
set -euo pipefail

ROLE="${KLOWB_DB_ROLE:-klowb}"
PASSWORD="${KLOWB_DB_PASSWORD:-klowb}"
DATABASES=("${KLOWB_DB_NAME:-klowb}" "${KLOWB_TEST_DB_NAME:-klowb_test}")

run_psql() {
  if [ "$(id -u)" -eq 0 ]; then
    su postgres -c "psql -v ON_ERROR_STOP=1 -qtAX $*"
  else
    sudo -u postgres psql -v ON_ERROR_STOP=1 -qtAX "$@"
  fi
}

if [ "$(run_psql -c "\"SELECT 1 FROM pg_roles WHERE rolname='${ROLE}'\"")" != "1" ]; then
  run_psql -c "\"CREATE ROLE ${ROLE} LOGIN PASSWORD '${PASSWORD}'\""
  echo "created role ${ROLE}"
else
  echo "role ${ROLE} exists"
fi

for db in "${DATABASES[@]}"; do
  if [ "$(run_psql -c "\"SELECT 1 FROM pg_database WHERE datname='${db}'\"")" != "1" ]; then
    run_psql -c "\"CREATE DATABASE ${db} OWNER ${ROLE}\""
    echo "created database ${db}"
  else
    echo "database ${db} exists"
  fi
done
