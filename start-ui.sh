#!/usr/bin/env bash

scriptPath=$(dirname "$(readlink -f "$0")")
cd ${scriptPath}/

[[ ! -z "${GUNICORN_PORT}" ]] || GUNICORN_PORT="6060"
[[ ! -z "${GUNICORN_HOST}" ]] || GUNICORN_HOST="0.0.0.0"
[[ ! -z "${GUNICORN_WORKERS}" ]] || GUNICORN_WORKERS="1"
[[ ! -z "${GUNICORN_THREADS}" ]] || GUNICORN_THREADS="4"
[[ ! -z "${GUNICORN_TIMEOUT}" ]] || GUNICORN_TIMEOUT="240" # this needs to be tuned based on the network bandwidth

[[ ! -z "${SERVICE_LOG_LEVEL}" ]] || SERVICE_LOG_LEVEL="debug"

[[ ! -z "${SERVICE_AM_HOSTNAME}" ]] || SERVICE_AM_HOSTNAME=$(hostname)
[[ ! -z "${SERVICE_AM_PORT}" ]] || SERVICE_AM_PORT="6080"

echo "Environment variables:"
echo "  GUNICORN_PORT=${GUNICORN_PORT}"
echo "  GUNICORN_HOST=${GUNICORN_HOST}"
echo "  GUNICORN_WORKERS=${GUNICORN_WORKERS}"
echo "  GUNICORN_THREADS=${GUNICORN_THREADS}"
echo ""
echo "  SERVICE_LOG_LEVEL=${SERVICE_LOG_LEVEL}"
echo "  SERVICE_AM_HOSTNAME=${SERVICE_AM_HOSTNAME}"
echo "  SERVICE_AM_PORT=${SERVICE_AM_PORT}"
echo ""

## did you activate the virtual environment and install the requirements?
exec gunicorn --bind "${GUNICORN_HOST}:${GUNICORN_PORT}" --workers ${GUNICORN_WORKERS} --threads ${GUNICORN_THREADS} --timeout ${GUNICORN_TIMEOUT} \
        "ui:setup_ui(logging_level='${SERVICE_LOG_LEVEL}', backend_url='http://${SERVICE_AM_HOSTNAME}:${SERVICE_AM_PORT}/')"