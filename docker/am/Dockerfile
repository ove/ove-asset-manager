FROM jamiehewland/alpine-pypy:3
LABEL maintainer="o.serban@imperial.ac.uk"

WORKDIR /code

COPY common/ common/
COPY am/ am/
COPY start-am.sh .
COPY requirements.am.txt .

RUN apk add --no-cache bash && \
    apk add --no-cache --virtual build-base gcc && \
    apk add --no-cache libffi-dev libressl-dev musl-dev && \
    pip install --upgrade pip && \
    pip install -r requirements.am.txt && \
    apk del build-base gcc

CMD ["./start-am.sh"]