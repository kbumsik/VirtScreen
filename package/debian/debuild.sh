#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $DIR/_common.sh

cd package/debian/build
cd virtscreen-$PKGVER
dpkg-buildpackage -b
