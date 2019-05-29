FROM jamiehewland/alpine-pypy:3
LABEL maintainer="o.serban@imperial.ac.uk"

# this file was inspired by: https://github.com/jcupitt/docker-builds/tree/master/pyvips-alpine

RUN apk add --no-cache bash
RUN apk --no-cache add --virtual build-base autoconf automake

ARG VIPS_VERSION=8.8.0
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

WORKDIR /tmp/vips-${VIPS_VERSION}

RUN ./configure --prefix=/usr --disable-static --disable-debug && make V=0 && make install

WORKDIR /tmp
RUN rm -rf /tmp/vips-${VIPS_VERSION}

RUN apk del build-base autoconf automake

CMD ["bash"]