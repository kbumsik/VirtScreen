#!/bin/bash

# Get parameters. Just return 0 if no parameter passed
if [ -n "$1" ]; then
    VERSION=$1
else
    exit 0
fi

# Directory
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ROOT=$DIR/..

override_version () {
    # Update python setup.py
    perl -pi -e "s/version=\'\d+\.\d+\.\d+\'/version=\'$VERSION\'/" \
    		$ROOT/setup.py
    # Update .json files in the module
    perl -pi -e "s/\"version\"\s*\:\s*\"\d+\.\d+\.\d+\"/\"version\"\: \"$VERSION\"/" \
    		$ROOT/virtscreen/assets/data.json
    perl -pi -e "s/\"version\"\s*\:\s*\"\d+\.\d+\.\d+\"/\"version\"\: \"$VERSION\"/" \
    		$ROOT/virtscreen/assets/config.default.json
    # Arch AUR
    perl -pi -e "s/pkgver=\d+\.\d+\.\d+/pkgver=$VERSION/" \
    		$ROOT/package/archlinux/PKGBUILD
    # Debian
    perl -pi -e "s/PKGVER=\d+\.\d+\.\d+/PKGVER=$VERSION/" \
    		$ROOT/package/debian/_common.sh
}

build_pypi () {
    make -C $ROOT package/pypi/virtscreen-$VERSION-py2.py3-none-any.whl
}

build_appimage () {
    make -C $ROOT package/appimage/VirtScreen-x86_64.AppImage
}

build_debian () {
    make -C $ROOT package/debian/virtscreen_$VERSION-1_all.deb
}

override_version
build_pypi
build_appimage
build_debian
