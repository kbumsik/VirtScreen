# See https://packaging.python.org/tutorials/distributing-packages/#packaging-your-project
# for python packaging reference.
VERSION ?= 0.2.4

DOCKER_NAME=kbumsik/virtscreen
DOCKER_RUN=docker run --interactive --tty -v $(shell pwd):/app $(DOCKER_NAME)
DOCKER_RUN_TTY=docker run --interactive --tty -v $(shell pwd):/app $(DOCKER_NAME)

.ONESHELL:

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

package/appimage/%.AppImage:
	$(DOCKER_RUN) package/appimage/build.sh
	$(DOCKER_RUN) chown -R $(shell id -u):$(shell id -u) package/appimage

appimage-clean:
	-rm -rf package/appimage/virtscreen.AppDir package/appimage/VirtScreen-x86_64.AppImage

# For Debian packaging, https://www.debian.org/doc/manuals/debmake-doc/ch08.en.html#setup-py
.PHONY: deb-contents deb-clean

package/debian/%.deb:
	$(DOCKER_RUN) package/debian/debmake.sh
	$(DOCKER_RUN) package/debian/copy_debian.sh
	$(DOCKER_RUN) package/debian/debuild.sh
	$(DOCKER_RUN) chown -R $(shell id -u):$(shell id -u) package/debian/build
	cp package/debian/build/virtscreen*.deb package/debian

deb-contents:
	$(DOCKER_RUN) dpkg -c package/debian/*.deb

deb-clean:
	rm -rf package/debian/build package/debian/*.deb

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
			package/debian/_common.sh

# Clean packages
clean: appimage-clean arch-clean deb-clean wheel-clean
