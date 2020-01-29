#!/bin/zsh

set -euo pipefail

. toolchain/build_settings.conf

NAME="sip"
VERSION="4.19.18"
VERIFY_FILE="$DISTDIR/usr/bin/sip"
DOWNLOAD_ADDR="https://www.riverbankcomputing.com/static/Downloads/sip/${VERSION}/${NAME}-${VERSION}.tar.gz"
DOWNLOAD_FILE="${DOWNLOADDIR}/${NAME}-${VERSION}.tar.gz"

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

  #sed -i '' 's/PyStringCheck/PyString_Check/g' siplib/siplib.c
  #python configure.py --bindir=${DISTDIR}/usr/bin --sip-module PyQt5.sip
  python configure.py --bindir=${DISTDIR}/usr/bin
  make ${MAKE_JOBS}
  make install

  cd $ROOT_DIR
else
  echo "${NAME} already installed."
fi
