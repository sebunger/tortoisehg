#!/bin/zsh

set -euo pipefail

. toolchain/build_settings.conf

NAME="qt-everywhere-opensource-src"
VERSION="4.8.6"
VERIFY_FILE="$DISTDIR/usr/bin/qmake"
DOWNLOAD_ADDR="http://download.qt.io/official_releases/qt/4.8/${VERSION}/${NAME}-${VERSION}.tar.gz"
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

  ./configure \
    -prefix "${DISTDIR}/usr/share/qt" \
    -bindir "${DISTDIR}/usr/bin" \
    -libdir "${DISTDIR}/usr/lib" \
    -confirm-license \
    -opensource \
    -release \
    -optimized-qmake \
    -no-qt3support \
    -no-phonon \
    -no-webkit \
    -no-javascript-jit \
    -no-multimedia \
    -no-declarative \
    -no-declarative-debug \
    -no-script \
    -no-scripttools \
    -no-xmlpatterns \
    -nomake demos \
    -nomake examples \
    -nomake tools \
    -nomake docs \
    -no-avx \
    -no-ssse3 \
    -no-sse4.1 \
    -no-sse4.2 \
    -arch x86_64

  make ${MAKE_JOBS}
  make install

  cd $ROOT_DIR
else
  echo "${NAME} already installed."
fi
