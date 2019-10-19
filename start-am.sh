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

[[ ! -z "${GUNICORN_PORT}" ]] || GUNICORN_PORT="6080"
[[ ! -z "${GUNICORN_HOST}" ]] || GUNICORN_HOST="0.0.0.0"
[[ ! -z "${GUNICORN_WORKERS}" ]] || GUNICORN_WORKERS="1"
[[ ! -z "${GUNICORN_THREADS}" ]] || GUNICORN_THREADS="4"
[[ ! -z "${GUNICORN_TIMEOUT}" ]] || GUNICORN_TIMEOUT="240" # this needs to be tuned based on the network bandwidth

[[ ! -z "${SERVICE_LOG_LEVEL}" ]] || SERVICE_LOG_LEVEL="debug"
[[ ! -z "${SERVICE_CONFIG}" ]] || SERVICE_CONFIG="config/credentials.json"
[[ ! -z "${AUTH_CONFIG}" ]] || AUTH_CONFIG="config/auth.json"
[[ ! -z "${WORKER_CONFIG}" ]] || WORKER_CONFIG="config/worker.json"

echo "Environment variables:"
echo "  GUNICORN_PORT=${GUNICORN_PORT}"
echo "  GUNICORN_HOST=${GUNICORN_HOST}"
echo "  GUNICORN_WORKERS=${GUNICORN_WORKERS}"
echo "  GUNICORN_THREADS=${GUNICORN_THREADS}"
echo ""
echo "  SERVICE_LOG_LEVEL=${SERVICE_LOG_LEVEL}"
echo "  SERVICE_CONFIG=${SERVICE_CONFIG}"
echo "  AUTH_CONFIG=${AUTH_CONFIG}"
echo "  WORKER_CONFIG=${WORKER_CONFIG}"
echo ""

## did you activate the virtual environment and install the requirements?
exec gunicorn --bind "${GUNICORN_HOST}:${GUNICORN_PORT}" --workers ${GUNICORN_WORKERS} --threads ${GUNICORN_THREADS} \
  --timeout ${GUNICORN_TIMEOUT} \
  "am:setup_app(credentials_config='${SERVICE_CONFIG}', auth_config='${AUTH_CONFIG}', worker_config='${WORKER_CONFIG}', logging_level='${SERVICE_LOG_LEVEL}')"
