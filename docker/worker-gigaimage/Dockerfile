FROM jamiehewland/alpine-pypy:3
LABEL maintainer="david.akroyd07@imperial.ac.uk"

# this file was inspired by: https://github.com/jcupitt/docker-builds/tree/master/pyvips-alpine

WORKDIR /code

ADD common/ common/
ADD workers/__init__.py workers/
ADD workers/base/ workers/base/
ADD workers/gigaimage/ workers/gigaimage/

ADD start-worker.sh .
ADD requirements.txt .

RUN apk add --no-cache bash
RUN apk --no-cache add --virtual build-base autoconf automake

ARG VIPS_VERSION=8.7.4
ARG VIPS_URL=https://github.com/libvips/libvips/releases/download

RUN apk update && apk upgrade

# basic packages libvips likes
# we need to figure out the dependencies we need
RUN apk add \
    libtool \
    bc \
	zlib-dev \
	expat-dev \
	jpeg-dev \
	tiff-dev \
	glib-dev \
	libjpeg-turbo-dev \
	libexif-dev \
	lcms2-dev \
	fftw-dev \
	giflib-dev \
	libpng-dev \
	libwebp-dev \
    libgsf-dev

RUN wget -O- ${VIPS_URL}/v${VIPS_VERSION}/vips-${VIPS_VERSION}.tar.gz | tar xzC /tmp
RUN cd /tmp/vips-${VIPS_VERSION} \
	&& ./configure --prefix=/usr --disable-static --disable-debug \
	&& make V=0 \
	&& make install

RUN pip install -r requirements.txt && pip install pyvips

RUN apk del build-base autoconf automake

ENV WORKER_CLASS "workers.gigaimage.ImageWorker"
CMD "./start-worker.sh"