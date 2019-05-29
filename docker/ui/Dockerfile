FROM node:alpine as builder

WORKDIR /code

COPY package.json .
COPY move-assets.js .

RUN npm install && npm run move-assets

FROM jamiehewland/alpine-pypy:3
LABEL maintainer="o.serban@imperial.ac.uk"

WORKDIR /code

# copy the javascript libraries according to package.json
COPY --from=builder /code/ui/ ui/

COPY common/ common/
COPY ui/ ui/
COPY docs/ docs/
COPY start-ui.sh .
COPY requirements.ui.txt .

RUN apk add --no-cache bash

RUN pip install -r requirements.ui.txt

CMD ["./start-ui.sh"]