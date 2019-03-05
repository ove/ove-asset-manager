# AM UI Configuration options

All configuration options can be passed using environment variables, passed to the docker image or directly to
the **start-ui.sh** script:

- **GUNICORN_PORT**: the service port, defaults to 6060.
- **GUNICORN_HOST**: the bind address, defaults to 0.0.0.0.
- **GUNICORN_WORKERS**: number of workers to spawn, defaults to 1. The workers are processes and if you're 
using CPython or PyPy it is safe to use threads instead. For regular Python the number of workers should be
increased and the number of threads should be set to 1, as Python is not thread safe.
- **GUNICORN_THREADS**: max number of threads to spin, defaults to 4. Can be adjusted based on the number of 
CPUs available on the machine. 
- **GUNICORN_TIMEOUT**: the request timeout, defaults to 240. This needs to be tuned based on the network bandwidth.
- **SERVICE_LOG_LEVEL**: logging level using standard Python logging names, defaults to debug.
- **SERVICE_AM_HOSTNAME**: the backend service backend url, defaults to system hostname
- **SERVICE_AM_PORT**: the backend service port, defaults to 6080
