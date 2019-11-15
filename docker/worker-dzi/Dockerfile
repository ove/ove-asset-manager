FROM ovehub/alpine-pypy-vips:8.8.3
LABEL maintainer="o.serban@imperial.ac.uk"

ARG PYVIPS_VERSION=2.1.8

WORKDIR /code

COPY common/ common/
COPY workers/__init__.py workers/
COPY workers/base/ workers/base/
COPY workers/dzi/ workers/dzi/

COPY start-worker.sh .
COPY requirements.worker.txt .

RUN apk add --no-cache bash

RUN apk --no-cache add --virtual build-base && \
    pip install --upgrade pip && \
    pip install -r requirements.worker.txt && \
    pip install pyvips==${PYVIPS_VERSION} && \
    apk del build-base

ENV WORKER_CLASS "workers.dzi.DeepZoomImageWorker"
ENV GUNICORN_PORT "6091"

CMD ["./start-worker.sh"]