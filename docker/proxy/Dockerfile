FROM jamiehewland/alpine-pypy:3
LABEL maintainer="o.serban@imperial.ac.uk"

WORKDIR /code

COPY common/ common/
COPY proxy/ proxy/
COPY start-proxy.sh .
COPY requirements.txt .

RUN apk add --no-cache bash

RUN pip install -r requirements.txt

CMD ["./start-proxy.sh"]