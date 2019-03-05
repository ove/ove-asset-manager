# Install Guide

## Docker using the OVE Installer

The easiest option to run all the services is to use the [OVE Installer](https://github.com/ove/ove-install)
that allows you to configure all the services interactively.

## S3 Store - MINIO Configuration

This step is **optional**. If you already have a S3 store please skip this step.

The Asset Manager was tested against an open source implementation of S3 protocol called [MINIO](http://minio.io/).

The docker-compose configuration to spin up a MINIO instance is:

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

While this docker setup is perfect for testing and could handle well production, it is highly recommended to configure
the store on a bare-metal install. Please see the [MINIO install guide](https://docs.minio.io/) for more details.

## Docker without installer

In this guide, docker-compose will be used to simplify the syntax. All the configuration is available in plain
docker, but the syntax should be longer and sometimes less clear.

In the **docker-compose.yml** bellow, the service is configured for production use. If you wish to enable different 
options please check the documentation for each service for all the available settings.

**Note:** Please set the **service version** parameter before running the config. Also, the AM service requires a 
config file to run. Please refer to the AM Backend configuration for more details.

A template of the config file can be found in **config/credentials.template.json** which can be saved as 
**config/credentials.json**. The configuration requires an existing S3 store, if you require one please read the 
[MINIO configuration](#s3-store---minio-configuration) section. 

```yaml
version: '3'
services:
  ovehub-ove-asset-manager-service:
    image: ovehub/ove-asset-manager-service:${service-version}
    ports:
      - "6080:6080"
    volumes:
      - ./config/:/code/config/:ro
    environment:
      GUNICORN_THREADS: "8"
      SERVICE_LOG_LEVEL: "info"

  ovehub-ove-asset-manager-worker-zip:
    image: ovehub/ove-asset-manager-worker-zip:${service-version}
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
    image: ovehub/ove-asset-manager-ui:${service-version}
    ports:
      - "6060:6060"
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


## Non-docker installs

All the services can can run perfectly on bare-metal Linux or MacOS as well. To start please clone this repository
or download a release.

The services have been tested on CPython 3.6 and PyPy3.6 v7.0. For better performance PyPy is recommended, but
for convenience CPython can be also used. It is highly recommended to avoid Python if possible because of poor
performance.

A virtual environment can be created by executing:

```bash
virtualenv -p python3 env && source env/bin/activate
```

The dependencies can be installed safely within the same virtual environment (please make sure that the virtual
environment is active, e.g. the terminal should display something like **env** at the beginning of the line):

```bash
pip -r requirements.txt && pip -r requirements.ui.txt
```

If you wish to install the Deep Zoom Worker, the pyvips needs to be installed in the virtual environment as well. 
Please check the [install guide](https://libvips.github.io/pyvips/README.html#install) for details on how to 
install the library and the system bindings.

To start the AM Backend:

```bash
./start-am.sh
```

UI:

The UI requires a few JavaScript libraries to be downloaded before started (this has to be executed in the root folder):

```bash
npm install
```

If the command is successful all the web assets will be downloaded into **ui/static/vendors/**. If the folder is empty after 
execution of the npm command, please check the execution logs for more details.

After downloading all the web assets, it is safe to delete the **node_modules** folder.

To start the UI:

```bash
./start-ui.sh
```

Deep Zoom Worker:

```bash
 WORKER_CLASS="workers.gigaimage.ImageWorker" ./start-worker.sh
```

Zip worker:

```bash
 WORKER_CLASS="workers.zip.ZipWorker" ./start-worker.sh
```
