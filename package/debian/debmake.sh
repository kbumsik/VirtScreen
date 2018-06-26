#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $DIR/_common.sh

mkdir -p package/debian/build
cd package/debian/build
# Download, rename, and copy files
wget -q https://github.com/kbumsik/VirtScreen/archive/$PKGVER.tar.gz
tar -xzmf $PKGVER.tar.gz
mv VirtScreen-$PKGVER virtscreen-$PKGVER
mv $PKGVER.tar.gz virtscreen-$PKGVER.tar.gz
cd virtscreen-$PKGVER
cp -f ../../Makefile Makefile
# call debmake
debmake -b':sh'
