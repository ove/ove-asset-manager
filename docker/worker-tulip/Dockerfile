FROM python:3-slim
LABEL maintainer="j.scott-brown@imperial.ac.uk"

WORKDIR /code

COPY common/ common/
COPY workers/__init__.py workers/
COPY workers/base/ workers/base/
COPY workers/tulip/ workers/tulip/

COPY start-worker.sh .
COPY requirements.worker.txt .

RUN apt-get update && apt-get upgrade && \
    apt-get install -y binutils && \
    apt-get install -y build-essential && \
    pip install --upgrade pip && \
    pip install -r requirements.worker.txt && \
    pip install tulip-python && \
    apt-get remove -y build-essential && \
    apt-get autoremove -y

ENV WORKER_CLASS "workers.tulip.NetworkWorker"
ENV GUNICORN_PORT "6092"

CMD ["./start-worker.sh"]