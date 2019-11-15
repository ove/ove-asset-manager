FROM jamiehewland/alpine-pypy:3
LABEL maintainer="o.serban@imperial.ac.uk"

# this file was inspired by: https://github.com/jcupitt/docker-builds/tree/master/pyvips-alpine
# OpenSlide inspiration: https://github.com/jcupitt/docker-builds/blob/master/libvips-openslide-alpine

RUN apk add --no-cache bash
RUN apk --no-cache add --virtual build-base autoconf automake

ARG VIPS_VERSION=8.8.3
ARG VIPS_URL=https://github.com/libvips/libvips/releases/download

ARG OPENSLIDE_VERSION=3.4.1
ARG OPENSLIDE_URL=https://github.com/openslide/openslide/releases/download

RUN apk update && apk upgrade

# basic packages libvips likes
# we need to figure out the dependencies we need
RUN apk add \
    libtool \
    bc \
	zlib-dev \
	expat-dev \
	jpeg-dev \
	openjpeg-dev \
	tiff-dev \
	gdk-pixbuf-dev \
	glib-dev \
	libjpeg-turbo-dev \
	libexif-dev \
	lcms2-dev \
	fftw-dev \
	giflib-dev \
	libpng-dev \
	libwebp-dev \
    libgsf-dev \
	libxml2-dev \
	orc-dev \
	poppler-dev \
	librsvg-dev \
	openexr-dev \
	sqlite-dev


WORKDIR /tmp

COPY openslide-init.patch .
RUN wget -O- ${OPENSLIDE_URL}/v${OPENSLIDE_VERSION}/openslide-${OPENSLIDE_VERSION}.tar.gz | tar xzC /tmp \
	&& patch -p0 < openslide-init.patch

WORKDIR /tmp/openslide-${OPENSLIDE_VERSION}

RUN ./configure && make && make install

RUN wget -O- ${VIPS_URL}/v${VIPS_VERSION}/vips-${VIPS_VERSION}.tar.gz | tar xzC /tmp

WORKDIR /tmp/vips-${VIPS_VERSION}

RUN ./configure --prefix=/usr --disable-static --disable-debug && make V=0 && make install

WORKDIR /tmp
RUN rm -rf /tmp/vips-${VIPS_VERSION}
RUN rm -rf /tmp/openslide-${OPENSLIDE_VERSION}
RUN rm -rf /tmp/openslide-init.patch

RUN apk del build-base autoconf automake

CMD ["bash"]