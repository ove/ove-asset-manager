FROM node:alpine as builder

WORKDIR /code

ADD package.json .
ADD move-assets.js .

RUN npm install && npm run move-assets

FROM jamiehewland/alpine-pypy:3
LABEL maintainer="o.serban@imperial.ac.uk"

WORKDIR /code

# copy the javascript libraries according to package.json
COPY --from=builder /code/ui/ ui/

ADD common/ common/
ADD ui/ ui/
ADD docs/ docs/
ADD start-ui.sh .
ADD requirements.ui.txt .

RUN apk add --no-cache bash

RUN pip install -r requirements.ui.txt

CMD ["./start-ui.sh"]