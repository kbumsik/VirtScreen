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
    make -C $ROOT python-wheel
}

build_arch () {
    wget -q https://github.com/kbumsik/VirtScreen/archive/$VERSION.tar.gz
    SHA256=$(sha256sum $VERSION.tar.gz | cut -d' ' -f1)
    # Arch AUR
    perl -pi -e "s/sha256sums=\('.*'\)/sha256sums=('$SHA256')/" \
    		$ROOT/package/archlinux/PKGBUILD
    rm $VERSION.tar.gz
    make -C $ROOT arch-upload
}

build_debian () {
    make -C $ROOT deb-env-build
    make -C $ROOT deb-chown
}

override_version
# build_pypi
build_arch
build_debian
