#!/bin/zsh

set -euo pipefail

. toolchain/build_settings.conf

NAME="openssl"
VERSION="1.0.2o"
VERIFY_FILE=$DISTDIR/usr/lib/libcrypto.a
DOWNLOAD_ADDR=https://www.openssl.org/source/${NAME}-${VERSION}.tar.gz
DOWNLOAD_FILE=${DOWNLOADDIR}/${NAME}-${VERSION}.tar.xz

if [ ! -f $VERIFY_FILE ]; then

  if [ ! -f $DOWNLOAD_FILE ]; then
    echo "Downloading ${DOWNLOAD_ADDR}"
    curl -L $DOWNLOAD_ADDR --output ${DOWNLOAD_FILE}
  fi

  rm -rf ${BUILDDIR}/${NAME}-${VERSION}
  mkdir -p ${BUILDDIR}

  if [ ! -d ${BUILDDIR}/${NAME}-${VERSION} ]; then
    echo "Extracting ${DOWNLOAD_FILE}"
    cd ${BUILDDIR}
    tar -xf ${DOWNLOAD_FILE}
    cd ${NAME}-${VERSION}
  else
    cd ${BUILDDIR}/${NAME}-${VERSION}
  fi

  export CC="clang"
  export CXX="clang++"

  ./Configure \
    --prefix="${DISTDIR}/usr" \
    --openssldir="${DISTDIR}/etc/openssl" \
    no-ssl2  \
    zlib-dynamic  \
    shared  \
    enable-cms  \
    darwin64-x86_64-cc  \
    enable-ec_nistp_64_gcc_128

  make depend
  make ${MAKE_JOBS}
  make install

  cd $ROOT_DIR
else
  echo "openssl installation found."
fi
