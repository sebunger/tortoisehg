#!/usr/bin/env bash

# Older versions of Qt have frameworks that can't be signed on 10.9.5 and
# later.  All that is required though is a slight massaging of the directory
# structure to make codesign happy.  Newer versions of Qt have the correct
# structure, but may not run on older systems (especially built from source on
# a newer system).

set -e

function updateframework()
{
	local name
	name="$(basename "${1}" ".framework")"

	if [[ -d "${fw}/Contents" ]]; then
		mv "${1}/Contents" "${1}/Versions/Current/"
	fi
	rm -f "${1}/${name}" "${1}/${name}_debug.prl" "${1}/${name}.prl"
}


THG_APP="${1:-${PWD}/dist/app/TortoiseHg.app}"

MACOS_DIR="${THG_APP}/Contents/MacOS"
FRAMEWORKS_DIR="${THG_APP}/Contents/Frameworks"
PLUGINS_DIR="${THG_APP}/Contents/PlugIns"


if [[ -z "${CODE_SIGN_IDENTITY}" ]]; then
	echo "Identify a signing certificate with \$CODE_SIGN_IDENTITY" >& 2
	exit 1
fi

if [[ ! -d "${THG_APP}" ]]; then
	echo "$1 is not an app bundle" >& 2
	exit 1
fi

# Make Qt frameworks suitable for signing, if necessary
for fw in QtCore QtGui QtNetwork QtSvg QtXml; do
	fw="${FRAMEWORKS_DIR}/${fw}.framework"

	updateframework "${fw}"
done


# Since the libraries have the version encoded in the name, they can't be
# listed directly.
for fw in ${FRAMEWORKS_DIR}/*.dylib ${FRAMEWORKS_DIR}/*.framework ${PLUGINS_DIR}/*/*.dylib; do
	# qscinitilla2 has a symlink in here, so skip that

	if [[ -L "${fw}" ]]; then
		continue
	fi

	codesign -s "${CODE_SIGN_IDENTITY}" "${fw}"
done

codesign -s "${CODE_SIGN_IDENTITY}" "${MACOS_DIR}/python"

# This _seems_ to be the equivalent of signing 'TortoiseHg' in the MacOS dir.
codesign -s "${CODE_SIGN_IDENTITY}" "${THG_APP}"
