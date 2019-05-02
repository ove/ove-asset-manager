# Installing OVE Asset Manager

## Installation by running OVE installers

The easiest option to run all the services is to use the [OVE Installer](https://github.com/ove/ove-install)
that allows you to configure all the services interactively.

The installer creates a [Docker Compose](https://docs.docker.com/compose/install/) file for the Asset Manager services (the asset manager service, UI, asset workers, and [MinIO](http://minio.io/) instance), separate from the docker-compose file for the other OVE services.

### S3 Store - MinIO Configuration

This step is **optional**, and can be skipped if you already have a Amazon S3 compatible object store.

The Asset Manager was tested against [MinIO](http://minio.io/), an open object storage server.

The docker-compose configuration to spin up a [MinIO](http://minio.io/) instance is:

```yaml
version: '3'
services:
  minio-store:
    image: minio/minio:latest
    ports:
    - "9000:9000"
    volumes:
      - "minio-storage-data:/data"
    environment:
      MINIO_ACCESS_KEY: "MINIO_ACCESS_KEY"
      MINIO_SECRET_KEY: "MINIO_SECRET_KEY"
    command: server /data

volumes:
  minio-storage-data:
```

While this docker setup is perfect for testing, it is recommended to use a bare-metal install in production.
Please refer the [MinIO documentation](https://docs.minio.io/) for more details.

## Alternative installation for a Docker environment without using OVE installers

It is possible to run the Asset Manager services with Docker without using docker-compose. However, this guide uses docker-compose, as this allows the configuration to be expressed as blocks of [YAML](https://en.wikipedia.org/wiki/YAML), which is clearer than listing long Docker commands with many arguments.

In the example **docker-compose.yml** below, the service is configured for production use. If you wish to enable different options please check the documentation for each service.

**Note:** Please set the **service version** parameter before running the config.

The Asset Manager service requires a config file to run. A template of the config file can be found in **config/credentials.template.json**; this can be copied to **config/credentials.json** and modified as required (refer to the Asset Manager Backend configuration for more details).

If you do not have an existing S3 compatible object store, please read the [MinIO configuration](#s3-store---minio-configuration) section.

```yaml
version: '3'
services:
  ovehub-ove-asset-manager-service:
    image: ovehub/ove-asset-manager-service:stable
    ports:
      - "6080:6080"
    volumes:
      - ./config/:/code/config/:ro
    environment:
      GUNICORN_THREADS: "8"
      SERVICE_LOG_LEVEL: "info"

  ovehub-ove-asset-manager-proxy:
    image: ovehub/ove-asset-manager-proxy:stable
    ports:
      - "6081:6081"
    volumes:
      - ./config/:/code/config/:ro
    environment:
      GUNICORN_THREADS: "8"
      SERVICE_LOG_LEVEL: "info"

  ovehub-ove-asset-manager-worker-zip:
    image: ovehub/ove-asset-manager-worker-zip:stable
    environment:
      SERVICE_LOG_LEVEL: "info"
      SERVICE_AM_HOSTNAME: "ovehub-ove-asset-manager-service"
      SERVICE_AM_PORT: "6080"

  ovehub-ove-asset-manager-worker-gigaimage:
    image: dzi
    environment:
      SERVICE_LOG_LEVEL: "info"
      SERVICE_AM_HOSTNAME: "ovehub-ove-asset-manager-service"
      SERVICE_AM_PORT: "6080"

  ovehub-ove-asset-manager-ui:
    image: ovehub/ove-asset-manager-ui:stable
    ports:
      - "6060:6060"
    environment:
      SERVICE_LOG_LEVEL: "info"
      SERVICE_AM_HOSTNAME: "ovehub-ove-asset-manager-service"
      SERVICE_AM_PORT: "6080"

  ovehub-ove-asset-manager-worker-tulip:
    image: ovehub/ove-asset-manager-worker-tulip:stable
    environment:
      SERVICE_LOG_LEVEL: "info"
      SERVICE_AM_HOSTNAME: "ovehub-ove-asset-manager-service"
      SERVICE_AM_PORT: "6080" 

```

You can run this by executing:

```bash
docker-compose up -d
```

To shutdown all the docker images:

```bash
docker-compose down
```

## Installation for a non-Docker environment

All the services can can run perfectly on bare-metal Linux or MacOS as well. To start please clone this repository or download a release.

The services have been tested on CPython 3.6 and PyPy3.6 v7.0. For better performance [PyPy](https://pypy.org/) is recommended, but for convenience [CPython](https://en.wikipedia.org/wiki/CPython) (the default Python interpreter) can be used instead.

A virtual environment can be created by executing:

```bash
virtualenv -p python3 env && source env/bin/activate
```

The terminal should display something like **env** at the beginning of the line, indicating that the virtual environment is active. You can then safely install the dependencies within the same virtual environment:

```bash
pip -r requirements.txt && pip -r requirements.ui.txt
```

If you wish to install the Deep Zoom Worker, then `pyvips` needs to be installed in the virtual environment as well. Please check the [install guide](https://libvips.github.io/pyvips/README.html#install) for details on how to install the library and the system bindings.

To start the Asset Manager Backend:

```bash
./start-am.sh
```

### User Interface

To downloaded required JavaScript libraries, change directory to the root folder and execute:

```bash
npm install
```

If the command is successful all the web assets will be downloaded into **ui/static/vendors/**. If this folder is empty after execution of the `npm` command, then something has failed: please check the execution logs for more details.

After downloading all the web assets, it is safe to delete the **node_modules** folder.

To start the User Interface:

```bash
./start-ui.sh
```

### Workers

Deep Zoom worker:

```bash
 WORKER_CLASS="workers.gigaimage.ImageWorker" ./start-worker.sh
```

Zip worker:

```bash
 WORKER_CLASS="workers.zip.ZipWorker" ./start-worker.sh
```

Tulip graph layout worker:

```bash
 WORKER_CLASS="workers.tulip.NetworkWorker" ./start-worker.sh
```
