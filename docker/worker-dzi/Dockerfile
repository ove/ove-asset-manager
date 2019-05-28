FROM ovehub/alpine-pypy-vips:8.8.0
LABEL maintainer="david.akroyd07@imperial.ac.uk"

WORKDIR /code

ADD common/ common/
ADD workers/__init__.py workers/
ADD workers/base/ workers/base/
ADD workers/dzi/ workers/dzi/

ADD start-worker.sh .
ADD requirements.txt .

RUN apk add --no-cache bash

RUN apk --no-cache add --virtual build-base && \
    pip install -r requirements.txt && pip install pyvips && \
    apk del build-base

ENV WORKER_CLASS "workers.dzi.DeepZoomImageWorker"
ENV GUNICORN_PORT "6091"

CMD ["./start-worker.sh"]