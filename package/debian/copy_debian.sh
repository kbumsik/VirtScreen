#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $DIR/_common.sh

cp -f $DIR/control $DIR/build/virtscreen-$PKGVER/debian/
cp -f $DIR/README.Debian $DIR/build/virtscreen-$PKGVER/debian/
