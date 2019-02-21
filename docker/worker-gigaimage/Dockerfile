FROM jamiehewland/alpine-pypy:3
LABEL maintainer="david.akroyd07@imperial.ac.uk"

WORKDIR /code

ADD common/ common/
ADD workers/__init__.py workers/
ADD workers/base/ workers/base/
ADD workers/zip/ workers/zip/

ADD start-worker.sh .
ADD requirements.txt .

RUN apk add --no-cache bash

RUN apk --no-cache add --virtual build-base && \
    pip install -r requirements.txt && \
    pip install pyvips && \
    apk del build-base

ENV WORKER_CLASS "workers.gigaimage.ImageWorker"
CMD "./start-worker.sh"