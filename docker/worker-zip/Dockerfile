FROM jamiehewland/alpine-pypy:3
LABEL maintainer="o.serban@imperial.ac.uk"

WORKDIR /code

COPY common/ common/
COPY workers/__init__.py workers/
COPY workers/base/ workers/base/
COPY workers/zip/ workers/zip/

COPY start-worker.sh .
COPY requirements.worker.txt .

RUN apk add --no-cache bash

RUN pip install -r requirements.worker.txt

ENV WORKER_CLASS "workers.zip.ZipWorker"
ENV GUNICORN_PORT "6090"

CMD ["./start-worker.sh"]