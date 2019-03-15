FROM python:3-slim
LABEL maintainer="j.scott-brown@imperial.ac.uk"

WORKDIR /code

ADD common/ common/
ADD workers/__init__.py workers/
ADD workers/base/ workers/base/
ADD workers/tulip/ workers/tulip/

ADD start-worker.sh .
ADD requirements.txt .

RUN apt-get update && \
    apt-get install -y build-essential && \
    pip install -r requirements.txt && \
    pip install tulip-python && \
    apt-get remove -y build-essential && \
    apt-get autoremove -y

ENV WORKER_CLASS "workers.tulip.NetworkWorker"
CMD ["./start-worker.sh"]