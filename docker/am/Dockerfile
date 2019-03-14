FROM jamiehewland/alpine-pypy:3
LABEL maintainer="o.serban@imperial.ac.uk"

WORKDIR /code

ADD common/ common/
ADD am/ am/
ADD start-am.sh .
ADD requirements.txt .

RUN apk add --no-cache bash

RUN apk --no-cache add --virtual build-base && \
    pip install -r requirements.txt && \
    apk del build-base

CMD ["./start-am.sh"]