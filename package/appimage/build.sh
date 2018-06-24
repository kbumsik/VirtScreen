#!/bin/bash

# Directory
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ROOT=$DIR/../..

cd $ROOT/package/appimage
mkdir virtscreen.AppDir
cd virtscreen.AppDir
# Create virtualenv
install -d usr/share/virtscreen
source $HOME/miniconda/bin/activate && \
	conda create -y --copy --prefix usr/share/virtscreen/env python=3.6
# Install VirtScreen using pip
source $HOME/miniconda/bin/activate && \
	source activate usr/share/virtscreen/env && \
	pip install $ROOT
# Delete unnecessary installed files done by setup.py
rm -rf usr/share/virtscreen/env/lib/python3.6/site-packages/usr
# Copy desktop entry, icon, and AppRun
install -m 644 -D $ROOT/virtscreen.desktop \
		usr/share/applications/virtscreen.desktop
install -m 644 -D $ROOT/virtscreen.desktop \
		.
install -m 644 -D $ROOT/data/virtscreen.png \
		usr/share/pixmaps/virtscreen.png
install -m 644 -D $ROOT/data/virtscreen.png \
		.
install -m 755 -D $ROOT/package/appimage/AppRun \
		.
cd ..
appimagetool virtscreen.AppDir
