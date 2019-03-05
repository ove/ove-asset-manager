# AM Backend Configuration options

All configuration options can be passed using environment variables, passed to the docker image or directly to
the **start-am.sh** script:

- **GUNICORN_PORT**: the service port, defaults to 6080.
- **GUNICORN_HOST**: the bind address, defaults to 0.0.0.0.
- **GUNICORN_WORKERS**: number of workers to spawn, defaults to 1. The workers are processes and if you're 
using CPython or PyPy it is safe to use threads instead. For regular Python the number of workers should be
increased and the number of threads should be set to 1, as Python is not thread safe.
- **GUNICORN_THREADS**: max number of threads to spin, defaults to 4. Can be adjusted based on the number of 
CPUs available on the machine. 
- **GUNICORN_TIMEOUT**: the request timeout, defaults to 240. This needs to be tuned based on the network bandwidth.
- **SERVICE_LOG_LEVEL**: logging level using standard Python logging names, defaults to debug.
- **SERVICE_CONFIG**: path to the config file, defaults to config/credentials.json. In case you are using docker
secrets this can be changed based on your configuration.

A template of the configuration file, which describes the store connections, can be found in 
**config/credentials.template.json**:

```json
{
  "default": "playground",
  "stores": [
    {
      "name": "playground",
      "endpoint": "hostname of the object store",
      "proxyUrl": "hostname of the proxy url or object store",
      "accessKey": "store access key",
      "secretKey": "store secret key"
    }
  ]
}
```

- **default**: the default store name in case the query does not provide a store
- **stores**: list of stores available
    - **name**: name of the store, can be any alphanumeric symbol including - and _, without spaces and /
    - **endpoint**: the url of the data endpoint, currently only supporting s3 stores
    - **proxyUrl**: the url of the read proxy server or data endpoint, if the endpoint supports http
    - **accessKey** and **secretKey**: store access and secret key