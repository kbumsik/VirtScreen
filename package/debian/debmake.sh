#!/bin/bash

source _common.sh

mkdir build
cd build
# Download
wget https://github.com/kbumsik/VirtScreen/archive/$PKGVER.tar.gz
tar -xzmf $PKGVER.tar.gz
# rename packages
mv VirtScreen-$PKGVER virtscreen-$PKGVER
mv $PKGVER.tar.gz virtscreen-$PKGVER.tar.gz

cd virtscreen-$PKGVER
debmake -b':py3'
