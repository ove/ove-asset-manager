FROM jamiehewland/alpine-pypy:3
LABEL maintainer="o.serban@imperial.ac.uk"

WORKDIR /code

ADD common/ common/
ADD ui/ ui/
ADD start-ui.sh .
ADD requirements.ui.txt .

RUN apk add --no-cache bash

RUN apk --no-cache add --virtual build-base && \
    pip install -r requirements.ui.txt && \
    apk del build-base

CMD "./start-ui.sh"