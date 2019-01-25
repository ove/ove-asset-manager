#!/usr/bin/env bash

scriptPath=$(dirname "$(readlink -f "$0")")
cd ${scriptPath}/

[[ ! -z "${GUNICORN_PORT}" ]] || GUNICORN_PORT="8080"
[[ ! -z "${GUNICORN_HOST}" ]] || GUNICORN_HOST="0.0.0.0"
[[ ! -z "${GUNICORN_WORKERS}" ]] || GUNICORN_WORKERS="1"
[[ ! -z "${GUNICORN_THREADS}" ]] || GUNICORN_THREADS="4"

[[ ! -z "${SERVICE_LOG_LEVEL}" ]] || SERVICE_LOG_LEVEL="debug"
[[ ! -z "${SERVICE_CONFIG}" ]] || SERVICE_CONFIG="config/credentials.json"


echo "Environment variables:"
echo "  GUNICORN_PORT=${GUNICORN_PORT}"
echo "  GUNICORN_HOST=${GUNICORN_HOST}"
echo "  GUNICORN_WORKERS=${GUNICORN_WORKERS}"
echo "  GUNICORN_THREADS=${GUNICORN_THREADS}"
echo ""
echo "  SERVICE_LOG_LEVEL=${SERVICE_LOG_LEVEL}"
echo "  SERVICE_CONFIG=${SERVICE_CONFIG}"
echo ""

## did you activate the virtual environment and install the requirements?
gunicorn -b "${GUNICORN_HOST}:${GUNICORN_PORT}" -w ${GUNICORN_WORKERS} --threads ${GUNICORN_THREADS} \
        "am:setup_app(config_file='${SERVICE_CONFIG}', logging_level='${SERVICE_LOG_LEVEL}')"