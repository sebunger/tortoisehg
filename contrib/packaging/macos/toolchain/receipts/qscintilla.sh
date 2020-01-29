#!/bin/zsh

set -euo pipefail

. toolchain/build_settings.conf

NAME="QScintilla_gpl"
if [ ${QT_VERSION} = "qt5" ]; then
  VERSION="2.10.8"
  LIBRARY_VERIFY_FILE="$DISTDIR/usr/lib/libqscintilla2_qt5.dylib"
else
  VERSION="2.9.4"
  LIBRARY_VERIFY_FILE="$DISTDIR/usr/lib/libqscintilla2.dylib"
fi
BINDINGS_VERIFY_FILE="$DISTDIR/usr/share/qt/qsci/api/python/QScintilla2.api"
DOWNLOAD_ADDR="http://sourceforge.net/projects/pyqt/files/QScintilla2/QScintilla-${VERSION}/${NAME}-${VERSION}.tar.gz"
DOWNLOAD_FILE="${DOWNLOADDIR}/${NAME}-${VERSION}.tar.gz"

BUILD_LIBRARY=0
BUILD_BINDINGS=0

if [ ! -f $LIBRARY_VERIFY_FILE ]; then
  BUILD_LIBRARY=1
fi

if [ ! -f $BINDINGS_VERIFY_FILE ]; then
  # only build bindings if pyqt is installed
  if [ ${QT_VERSION} = "qt5" ] && [ -f ${DISTDIR}/usr/bin/pyuic5 ]; then
    BUILD_BINDINGS=1
  fi

  if [ ${QT_VERSION} = "qt4" ] && [ -f ${DISTDIR}/usr/bin/pyuic4 ]; then
    BUILD_BINDINGS=1
  fi
fi

if [ ${BUILD_LIBRARY} -eq 1 ] || [ ${BUILD_BINDINGS} -eq 1 ]; then
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

  if [ ${BUILD_LIBRARY} -eq 1 ]; then
    cd Qt4Qt5
    if [ ${QT_VERSION} = "qt5" ]; then
      qmake -spec macx-clang
    else
      qmake -spec macx-g++
    fi
    make ${MAKE_JOBS}
    make install
    cd -
  fi

  if [ ${BUILD_BINDINGS} -eq 1 ]; then
    cd Python
    if [ ${QT_VERSION} = "qt5" ]; then
      python configure.py --pyqt=PyQt5
    else
      python configure.py --pyqt=PyQt4
    fi
    make ${MAKE_JOBS}
    make install
    cd -
  fi

  cd $ROOT_DIR
else
  echo "${NAME} already installed."
fi
