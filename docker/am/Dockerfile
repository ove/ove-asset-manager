FROM jamiehewland/alpine-pypy:3
LABEL maintainer="o.serban@imperial.ac.uk"

WORKDIR /code

COPY common/ common/
COPY am/ am/
COPY start-am.sh .
COPY requirements.txt .

RUN apk add --no-cache bash

RUN pip install -r requirements.txt

CMD ["./start-am.sh"]