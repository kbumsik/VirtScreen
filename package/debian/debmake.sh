#!/bin/bash

PKGVER=0.1.2
# Required for debmake
DEBEMAIL="k.bumsik@gmail.com"
DEBFULLNAME="Bumsik Kim"
export DEBEMAIL DEBFULLNAME

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
