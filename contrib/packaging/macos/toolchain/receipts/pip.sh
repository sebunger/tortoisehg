#!/bin/zsh

set -euo pipefail

. toolchain/build_settings.conf

NAME="pip"
VERIFY_FILE="$DISTDIR/System/Library/Frameworks/Python.framework/Versions/Current/bin/pip"
DOWNLOAD_ADDR="http://bootstrap.pypa.io/get-pip.py"
DOWNLOAD_FILE="${DOWNLOADDIR}/get-pip.py"

if [ ! -f $VERIFY_FILE ]; then

  if [ ! -f $DOWNLOAD_FILE ]; then
    echo "Downloading ${DOWNLOAD_ADDR}"
    curl -L $DOWNLOAD_ADDR --output ${DOWNLOAD_FILE}
  fi

  python ${DOWNLOAD_FILE}

  cd $ROOT_DIR
else
  echo "${NAME} already installed."
fi
