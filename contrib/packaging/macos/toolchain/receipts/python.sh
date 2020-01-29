#!/bin/zsh

set -euo pipefail

. toolchain/build_settings.conf

NAME="Python"
VERSION="2.7.17"
VERIFY_FILE=$DISTDIR/usr/bin/python
DOWNLOAD_ADDR=https://www.python.org/ftp/python/${VERSION}/${NAME}-${VERSION}.tar.xz
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
  
  patch -p0 <<'EOT'
--- Makefile.pre.in.ORIG	2019-07-14 16:24:12.000000000 -0400
+++ Makefile.pre.in	2019-07-14 16:24:19.000000000 -0400
@@ -211,7 +211,7 @@
 # The task to run while instrument when building the profile-opt target
 # We exclude unittests with -x that take a rediculious amount of time to
 # run in the instrumented training build or do not provide much value.
-PROFILE_TASK=-m test.regrtest --pgo -x test_asyncore test_gdb test_multiprocessing test_subprocess
+PROFILE_TASK=-m test.regrtest --pgo -x test_asyncore test_gdb test_multiprocessing test_subprocess test_mailbox

 # report files for gcov / lcov coverage report
 COVERAGE_INFO=	$(abs_builddir)/coverage.info
EOT

  export CC="clang"
  export CXX="clang++"
  export CFLAGS="-Os -pipe -fno-common -fno-strict-aliasing -fwrapv -DENABLE_DTRACE -DMACOSX -DNDEBUG -I${DISTDIR}/usr/include -I${SDKROOT}/usr/include"
  export LDFLAGS="-L${DISTDIR}/usr/lib"

  ./configure \
    --prefix="${DISTDIR}/usr" \
    --mandir="${DISTDIR}/usr/share/man" \
    --infodir="${DISTDIR}/usr/share/info" \
    --enable-ipv6 \
    --with-threads \
    --enable-framework="${DISTDIR}/System/Library/Frameworks" \
    --enable-toolbox-glue \
    --enable-optimizations

  make ${MAKE_JOBS}
  make install

  cd $ROOT_DIR
else
  echo "Python installation found."
fi
