#!/bin/zsh

set -euo pipefail

. toolchain/build_settings.conf

cd src/thg

python setup.py clean
python setup.py build
python setup.py install
