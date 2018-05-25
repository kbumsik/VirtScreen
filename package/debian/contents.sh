#!/bin/bash

source _common.sh

cd build
dpkg -c virtscreen_$PKGVER-1_all.deb
