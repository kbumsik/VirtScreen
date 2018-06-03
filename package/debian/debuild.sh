#!/bin/bash

source _common.sh

cd build
cd virtscreen-$PKGVER
if [ $1 = "virtualenv" ]; then
    dpkg-buildpackage -b
else
    debuild
fi
