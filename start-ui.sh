#!/usr/bin/env bash

if [[ "$OSTYPE" == *darwin* ]]; then
  if command -v greadlink >/dev/null 2>&1; then
    scriptPath=$(dirname "$(greadlink -f "$0")")
  else
    echo "greadlink command not found"
    exit 1
  fi
else
  scriptPath=$(dirname "$(readlink -f "$0")")
fi
cd "${scriptPath}/" || exit 1

[[ ! -z "${GUNICORN_PORT}" ]] || GUNICORN_PORT="6060"
[[ ! -z "${GUNICORN_HOST}" ]] || GUNICORN_HOST="0.0.0.0"
[[ ! -z "${GUNICORN_WORKERS}" ]] || GUNICORN_WORKERS="1"
[[ ! -z "${GUNICORN_THREADS}" ]] || GUNICORN_THREADS="4"
[[ ! -z "${GUNICORN_TIMEOUT}" ]] || GUNICORN_TIMEOUT="240" # this needs to be tuned based on the network bandwidth

[[ ! -z "${SERVICE_LOG_LEVEL}" ]] || SERVICE_LOG_LEVEL="debug"

[[ ! -z "${SERVICE_AM_HOSTNAME}" ]] || SERVICE_AM_HOSTNAME=$(hostname)
[[ ! -z "${SERVICE_AM_PORT}" ]] || SERVICE_AM_PORT="6080"

[[ ! -z "${LAUNCHER_URL}" ]] || LAUNCHER_URL=$(hostname)

echo "Environment variables:"
echo "  GUNICORN_PORT=${GUNICORN_PORT}"
echo "  GUNICORN_HOST=${GUNICORN_HOST}"
echo "  GUNICORN_WORKERS=${GUNICORN_WORKERS}"
echo "  GUNICORN_THREADS=${GUNICORN_THREADS}"
echo ""
echo "  SERVICE_LOG_LEVEL=${SERVICE_LOG_LEVEL}"
echo "  SERVICE_AM_HOSTNAME=${SERVICE_AM_HOSTNAME}"
echo "  SERVICE_AM_PORT=${SERVICE_AM_PORT}"
echo "  LAUNCHER_URL=${LAUNCHER_URL}"
echo ""

## did you activate the virtual environment and install the requirements?
exec gunicorn --bind "${GUNICORN_HOST}:${GUNICORN_PORT}" --workers ${GUNICORN_WORKERS} --threads ${GUNICORN_THREADS} --timeout ${GUNICORN_TIMEOUT} \
  "ui:setup_ui(logging_level='${SERVICE_LOG_LEVEL}', backend_url='http://${SERVICE_AM_HOSTNAME}:${SERVICE_AM_PORT}/', launcher_url='${LAUNCHER_URL}')"
