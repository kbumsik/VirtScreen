#!/bin/bash

source _common.sh

mkdir build
cd build
# Download
wget -q https://github.com/kbumsik/VirtScreen/archive/$PKGVER.tar.gz
tar -xzmf $PKGVER.tar.gz
# rename packages
mv VirtScreen-$PKGVER virtscreen-$PKGVER
mv $PKGVER.tar.gz virtscreen-$PKGVER.tar.gz

cd virtscreen-$PKGVER
if [ $1 = "virtualenv" ]; then
    cp -f ../../Makefile.virtualenv Makefile
    debmake -b':sh'
else
    debmake -b':py3'
fi
