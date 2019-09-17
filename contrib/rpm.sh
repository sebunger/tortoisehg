#!/bin/sh

RPMBUILDDIR="rpmbuild"

while [ "$1" ]; do
    case "$1" in
    --rpmbuilddir )
        shift
        RPMBUILDDIR="$1"
        shift
        ;;
    --installhg )
        shift
        HGRPM="$1"
        shift
        ;;
    * )
       	echo "Invalid parameter $1!" 1>&2
        exit 1
        ;;
    esac
done

if [ ! -z "$HGRPM" ]; then
	sudo rpm -i $HGRPM
fi

mkdir -p ${RPMBUILDDIR}/{SOURCES,BUILD,RPMS,SRPMS,SPECS}
version=`hg parents --template '{sub(r".*:", "", latesttag)}+{latesttagdistance}'`
if [ `expr "$version" : '.*+0$'` -ne 0 ]; then
  # We are on a tagged version
  version=`expr "$version" : '\(.*\)+0$'`
  release='1'
else
  release=`hg parents --template '{node|short}'`
fi

hg archive -t tgz ${RPMBUILDDIR}/SOURCES/tortoisehg-$version.tar.gz
sed -e "s,^Version:.*,Version: $version," \
    -e "s,^Release:.*,Release: $release," \
    `dirname $0`/tortoisehg.spec > ${RPMBUILDDIR}/SPECS/tortoisehg.spec

rpmbuild --define "_topdir `pwd`/${RPMBUILDDIR}" -ba ${RPMBUILDDIR}/SPECS/tortoisehg.spec || exit 1
rm -rf ${RPMBUILDDIR}/BUILD/
ls -l ${RPMBUILDDIR}/{RPMS/*,SRPMS}/tortoisehg-*.rpm
