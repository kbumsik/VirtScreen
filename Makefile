# See https://packaging.python.org/tutorials/distributing-packages/#packaging-your-project
# for python packaging reference.
VERSION ?= 0.3.2

DOCKER_NAME=kbumsik/virtscreen
DOCKER_RUN=docker run --interactive --tty -v $(shell pwd):/app $(DOCKER_NAME)
DOCKER_RUN_TTY=docker run --interactive --tty -v $(shell pwd):/app $(DOCKER_NAME)

PKG_APPIMAGE=package/appimage/VirtScreen.AppImage
PKG_DEBIAN=package/debian/virtscreen.deb
ARCHIVE=virtscreen-$(VERSION).tar.gz

.ONESHELL:

.PHONY: run debug run-appimage debug-appimage

all: package/pypi/*.whl $(ARCHIVE) $(PKG_APPIMAGE) $(PKG_DEBIAN)

# Run script
run:
	python3 -m virtscreen

debug:
	QT_DEBUG_PLUGINS=1 QML_IMPORT_TRACE=1 python3 -m virtscreen --log=DEBUG

run-appimage: $(PKG_APPIMAGE)
	$<

debug-appimage: $(PKG_APPIMAGE)
	QT_DEBUG_PLUGINS=1 QML_IMPORT_TRACE=1 $< --log=DEBUG

# tar.gz
.PHONY: archive

archive $(ARCHIVE):
	git archive --format=tar.gz --prefix=virtscreen-$(VERSION)/ -o $@ HEAD

# Docker tools
.PHONY: docker docker-build

docker:
	$(DOCKER_RUN_TTY) /bin/bash

docker-build:
	docker build -f Dockerfile -t $(DOCKER_NAME) .

# Python wheel package for PyPI
.PHONY: wheel-clean

package/pypi/%.whl:
	python3 setup.py bdist_wheel --universal
	cp dist/* package/pypi
	-rm -rf build dist *.egg-info

wheel-clean:
	-rm package/pypi/virtscreen*.whl

# For AppImage packaging, https://github.com/AppImage/AppImageKit/wiki/Creating-AppImages
.PHONY: appimage-clean
.SECONDARY: $(PKG_APPIMAGE)

$(PKG_APPIMAGE):
	$(DOCKER_RUN) package/appimage/build.sh
	$(DOCKER_RUN) mv package/appimage/VirtScreen-x86_64.AppImage $@
	$(DOCKER_RUN) chown -R $(shell id -u):$(shell id -u) package/appimage

appimage-clean:
	-rm -rf package/appimage/virtscreen.AppDir $(PKG_APPIMAGE)

# For Debian packaging, https://www.debian.org/doc/manuals/maint-guide/index.en.html
#	https://www.debian.org/doc/manuals/debmake-doc/ch08.en.html#setup-py
.PHONY: deb-contents deb-clean

$(PKG_DEBIAN): $(PKG_APPIMAGE) $(ARCHIVE)
	$(DOCKER_RUN) package/debian/build.sh
	$(DOCKER_RUN) mv package/debian/*.deb $@
	$(DOCKER_RUN) chown -R $(shell id -u):$(shell id -u) package/debian

deb-contents: $(PKG_DEBIAN)
	$(DOCKER_RUN) dpkg -c $<

deb-clean:
	rm -rf package/debian/build package/debian/*.deb package/debian/*.buildinfo \
		package/debian/*.changes

# For AUR: https://wiki.archlinux.org/index.php/Python_package_guidelines
#  and: https://wiki.archlinux.org/index.php/Creating_packages
.PHONY: arch-upload arch-clean

arch-upload: package/archlinux/.SRCINFO
	cd package/archlinux
	git clone ssh://aur@aur.archlinux.org/virtscreen.git
	cp PKGBUILD virtscreen
	cp .SRCINFO virtscreen
	cd virtscreen
	git add --all
	git commit
	git push
	cd ..
	rm -rf virtscreen

package/archlinux/.SRCINFO:
	cd package/archlinux
	makepkg --printsrcinfo > .SRCINFO

arch-clean:
	cd package/archlinux
	-rm -rf pkg src *.tar* .SRCINFO

# Override version
.PHONY: override-version

override-version:
	# Update python setup.py
	perl -pi -e "s/version=\'\d+\.\d+\.\d+\'/version=\'$(VERSION)\'/" \
			setup.py
	# Update .json files in the module
	perl -pi -e "s/\"version\"\s*\:\s*\"\d+\.\d+\.\d+\"/\"version\"\: \"$(VERSION)\"/" \
			virtscreen/assets/data.json
	perl -pi -e "s/\"version\"\s*\:\s*\"\d+\.\d+\.\d+\"/\"version\"\: \"$(VERSION)\"/" \
			virtscreen/assets/config.default.json
	# Arch AUR
	perl -pi -e "s/pkgver=\d+\.\d+\.\d+/pkgver=$(VERSION)/" \
			package/archlinux/PKGBUILD
	# Debian
	perl -pi -e "s/PKGVER=\d+\.\d+\.\d+/PKGVER=$(VERSION)/" \
			package/debian/build.sh

# Clean packages
clean: appimage-clean arch-clean deb-clean wheel-clean
	-rm -f $(ARCHIVE)
