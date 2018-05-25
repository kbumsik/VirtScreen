#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $DIR/_common.sh

echo $DIR/{control,rules,README.Debian} $DIR/build/virtscreen-$PKGVER/debian
cp $DIR/{control,rules,README.Debian} $DIR/build/virtscreen-$PKGVER/debian
