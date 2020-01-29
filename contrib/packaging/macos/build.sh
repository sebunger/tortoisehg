#!/bin/zsh

set -euo pipefail

export APP_NAME="TortoiseHg"
export QT_VERSION="qt5"

rm -rf dist/TortoiseHg.app
mkdir -p toolchain/downloads

# build/verify dependencies
toolchain/receipts/openssl.sh
toolchain/receipts/python.sh
toolchain/receipts/pip.sh

if [ ${QT_VERSION} = "qt5" ]; then
  toolchain/receipts/qt5.sh
else
  toolchain/receipts/qt4.sh
fi
toolchain/receipts/qscintilla.sh
toolchain/receipts/sip.sh
if [ ${QT_VERSION} = "qt5" ]; then
  toolchain/receipts/pyqt5.sh
else
  toolchain/receipts/pyqt4.sh
fi

toolchain/receipts/qscintilla.sh
toolchain/receipts/packages.sh

# build mercurial + tortoisehg
toolchain/receipts/mercurial.sh
toolchain/receipts/tortoisehg.sh

# create application package
. toolchain/build_settings.conf

# CFVersion is always x.y.z format.  The plain version will have changeset info
# in non-tagged builds.
export THG_CFVERSION=`python -c 'from tortoisehg.util import version; print(version.package_version())'`
export THG_VERSION=`python -c 'from tortoisehg.util import version; print(version.version())'`

python setup.py

if [ -d dist/${APP_NAME}.app ]; then
  rm -rf build
  rm -rf toolchain/build

  if [ ${QT_VERSION} = "qt5" ]; then
    macdeployqt dist/${APP_NAME}.app -always-overwrite
    cp -R ${DISTDIR}/usr/lib/QtNetwork.framework dist/${APP_NAME}.app/Contents/Frameworks/
  fi

  if [ -n "${CODE_SIGN_IDENTITY-}" ]; then
    echo "Signing app bundle"
    src/thg/contrib/sign-py2app.sh dist/${APP_NAME}.app
  fi

  toolchain/receipts/createDmg.sh
fi
