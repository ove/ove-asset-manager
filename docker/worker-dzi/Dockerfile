FROM ovehub/alpine-pypy-vips:8.8.0
LABEL maintainer="david.akroyd07@imperial.ac.uk"

ARG PYVIPS_VERSION=2.1.6

WORKDIR /code

COPY common/ common/
COPY workers/__init__.py workers/
COPY workers/base/ workers/base/
COPY workers/dzi/ workers/dzi/

COPY start-worker.sh .
COPY requirements.txt .

RUN apk add --no-cache bash

RUN apk --no-cache add --virtual build-base && \
    pip install -r requirements.txt && pip install pyvips==${PYVIPS_VERSION} && \
    apk del build-base

ENV WORKER_CLASS "workers.dzi.DeepZoomImageWorker"
ENV GUNICORN_PORT "6091"

CMD ["./start-worker.sh"]