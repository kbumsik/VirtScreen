# See https://packaging.python.org/tutorials/distributing-packages/#packaging-your-project
# for python packaging reference.

DOCKER_NAME=kbumsik/virtscreen
DOCKER_RUN=docker run --interactive --tty -v $(shell pwd):/app $(DOCKER_NAME)
DOCKER_RUN_TTY=docker run --interactive --tty -v $(shell pwd):/app $(DOCKER_NAME)
DOCKER_RUN_DEB=docker run -v $(shell pwd)/package/debian:/app $(DOCKER_NAME)

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
	$(DOCKER_RUN_DEB) /app/debmake.sh virtualenv
	$(DOCKER_RUN_DEB) /app/copy_debian.sh virtualenv
	$(DOCKER_RUN_DEB) /app/debuild.sh virtualenv
	$(DOCKER_RUN_DEB) chown -R $(shell id -u):$(shell id -u) /app/build
	cp package/debian/build/virtscreen*.deb package/debian

deb-contents:
	$(DOCKER_RUN_DEB) /app/contents.sh

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

# Clean packages
clean: appimage-clean arch-clean deb-clean wheel-clean
