FROM maven:3-jdk-11 as builder
LABEL maintainer="o.serban@imperial.ac.uk"

WORKDIR /code

COPY proxy/src/ src/
COPY proxy/pom.xml .

RUN rm -rf target/ && mvn clean compile package

# The optimized docker image
FROM azul/zulu-openjdk-alpine:11-jre

RUN apk add --no-cache bash

ENV APPLICATION_PATH /app
ENV APPLICATION_USER gdo

RUN adduser -D -g '' $APPLICATION_USER && mkdir $APPLICATION_PATH && chown -R $APPLICATION_USER $APPLICATION_PATH
USER $APPLICATION_USER
WORKDIR $APPLICATION_PATH

COPY --from=builder /code/target/ove-am-kreadproxy-*-jar-with-dependencies.jar .
COPY start-proxy.sh .

CMD "./start-proxy.sh"
