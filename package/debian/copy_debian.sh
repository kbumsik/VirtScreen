#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $DIR/_common.sh

if [ $1 = "virtualenv" ]; then
    cp -f $DIR/control.virtualenv $DIR/build/virtscreen-$PKGVER/debian/control
    cp -f $DIR/README.Debian $DIR/build/virtscreen-$PKGVER/debian/
else
    cp -f $DIR/{control,rules,README.Debian} $DIR/build/virtscreen-$PKGVER/debian
fi
