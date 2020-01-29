#!/bin/zsh

set -euo pipefail

. toolchain/build_settings.conf

pip install -r toolchain/receipts/requirements.txt

if [ ${QT_VERSION} = "qt5" ]; then
  cp toolchain/patches/main-x86_64 ${DISTDIR}/System/Library/Frameworks/Python.framework/Versions/Current/lib/python2.7/site-packages/py2app/apptemplate/prebuilt
fi
