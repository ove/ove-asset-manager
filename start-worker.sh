#!/usr/bin/env bash

scriptPath=$(dirname "$(readlink -f "$0")")
cd ${scriptPath}/

[[ ! -z "${GUNICORN_PORT}" ]] || GUNICORN_PORT="9080"
[[ ! -z "${GUNICORN_HOST}" ]] || GUNICORN_HOST="0.0.0.0"
[[ ! -z "${GUNICORN_WORKERS}" ]] || GUNICORN_WORKERS="1"
[[ ! -z "${GUNICORN_THREADS}" ]] || GUNICORN_THREADS="4"
[[ ! -z "${GUNICORN_TIMEOUT}" ]] || GUNICORN_TIMEOUT="240" # this needs to be tuned based on the network bandwidth

[[ ! -z "${SERVICE_LOG_LEVEL}" ]] || SERVICE_LOG_LEVEL="debug"
[[ ! -z "${SERVICE_HOSTNAME}" ]] || SERVICE_HOSTNAME=$(hostname)

[[ ! -z "${SERVICE_AM_HOSTNAME}" ]] || SERVICE_AM_HOSTNAME=$(hostname)
[[ ! -z "${SERVICE_AM_PORT}" ]] || SERVICE_AM_PORT="8080"
[[ ! -z "${SERVICE_AM_ATTEMPTS}" ]] || SERVICE_AM_ATTEMPTS=5
[[ ! -z "${SERVICE_AM_TIMEOUT}" ]] || SERVICE_AM_TIMEOUT=5000

[[ ! -z "${WORKER_NAME}" ]] || WORKER_NAME=$(strings /dev/urandom | grep -o '[[:alnum:]]' | head -n 21 | tr -d '\n')
[[ ! -z "${WORKER_NAME}" ]] || WORKER_NAME=$(echo `cat /dev/urandom | base64 | tr -dc "[:alnum:]" | head -c10`)


# For testing purpose this can be used, otherwise the next line should be commented
 [[ ! -z "${WORKER_CLASS}" ]] || WORKER_CLASS="workers.gigaimage.ImageWorker"


echo "Environment variables:"
echo "  GUNICORN_PORT=${GUNICORN_PORT}"
echo "  GUNICORN_HOST=${GUNICORN_HOST}"
echo "  GUNICORN_WORKERS=${GUNICORN_WORKERS}"
echo "  GUNICORN_THREADS=${GUNICORN_THREADS}"
echo ""
echo "  SERVICE_LOG_LEVEL=${SERVICE_LOG_LEVEL}"
echo "  SERVICE_HOSTNAME=${SERVICE_HOSTNAME}"
echo ""
echo "  SERVICE_AM_HOSTNAME=${SERVICE_AM_HOSTNAME}"
echo "  SERVICE_AM_PORT=${SERVICE_AM_PORT}"
echo ""
echo "  WORKER_NAME=${WORKER_NAME}"
echo "  WORKER_CLASS=${WORKER_CLASS}"
echo ""

## did you activate the virtual environment and install the requirements?
gunicorn --bind "${GUNICORN_HOST}:${GUNICORN_PORT}" --workers ${GUNICORN_WORKERS} --threads ${GUNICORN_THREADS} --timeout ${GUNICORN_TIMEOUT} \
        "workers.base:setup_worker(logging_level='${SERVICE_LOG_LEVEL}', hostname='${SERVICE_HOSTNAME}', port='${GUNICORN_PORT}',
                                   service_url='http://${SERVICE_AM_HOSTNAME}:${SERVICE_AM_PORT}/api/workers',
                                   registration_attempts=${SERVICE_AM_ATTEMPTS}, registration_timeout=${SERVICE_AM_TIMEOUT},
                                   worker_name='${WORKER_NAME}', worker_class='${WORKER_CLASS}')"