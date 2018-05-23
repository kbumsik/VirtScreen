#!/bin/bash

PKGVER=0.1.2
# Required for debmake
DEBEMAIL="k.bumsik@gmail.com"
DEBFULLNAME="Bumsik Kim"
export DEBEMAIL DEBFULLNAME

cd build
cd virtscreen-$PKGVER
debuild
