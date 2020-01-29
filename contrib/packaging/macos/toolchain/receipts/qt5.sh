#!/bin/zsh

set -euo pipefail

. toolchain/build_settings.conf

NAME="qt-everywhere-opensource-src"
VERSION="5.9.8"
VERIFY_FILE="$DISTDIR/usr/bin/qmake"
DOWNLOAD_ADDR="http://download.qt.io/official_releases/qt/5.9/${VERSION}/single/${NAME}-${VERSION}.tar.xz"
DOWNLOAD_FILE="${DOWNLOADDIR}/${NAME}-${VERSION}.tar.xz"

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
    -nomake examples \
    -no-avx \
    -no-ssse3 \
    -no-sse4.1 \
    -no-sse4.2 \
    -skip qt3d \
    -skip qtquickcontrols \
    -skip qtquickcontrols2 \
    -skip qtwebengine \
    -skip qtwebview \
    -skip qtwebsockets \
    -skip qtconnectivity \
    -skip qtspeech \
    -skip qtscript \
    -skip qtserialbus \
    -skip qtserialport \
    -skip qtxmlpatterns \
    -skip qtmultimedia \
    -skip qtlocation \
    -skip qtgamepad \
    -skip qtdeclarative \
    -skip qtsensors \
    -skip qtwebchannel \
    -skip qtcanvas3d \
    -skip qtcharts \
    -skip qtdatavis3d \
    -skip qtpurchasing \
    -qt-zlib

  make ${MAKE_JOBS}
  make install

  cd $ROOT_DIR
else
  echo "${NAME} already installed."
fi
