# See https://packaging.python.org/tutorials/distributing-packages/#packaging-your-project
# for python packaging reference.

DOCKER_NAME=kbumsik/virtscreen

.PHONY:

python-wheel:
	/usr/bin/python3 setup.py bdist_wheel --universal

python-install:
	/usr/bin/pip3 install . --user

python-uninstall:
	/usr/bin/pip3 uninstall virtscreen
	
python-clean:
	rm -rf build dist virtscreen.egg-info virtscreen/qml/*.qmlc

pip-upload: python-wheel
	twine upload dist/*

.ONESHELL:

# Docker
docker-build:
	docker build -f Dockerfile -t $(DOCKER_NAME) .

docker:
	docker run --interactive --tty -v $(shell pwd)/package/debian:/app $(DOCKER_NAME) /bin/bash
	
docker-rm:
	docker image rm -f $(DOCKER_NAME)

docker-pull:
	docker pull $(DOCKER_NAME)

docker-push:
	docker login
	docker push $(DOCKER_NAME)

# For Debian packaging, https://www.debian.org/doc/manuals/debmake-doc/ch08.en.html#setup-py
deb-make:
	docker run -v $(shell pwd)/package/debian:/app $(DOCKER_NAME) /app/debmake.sh

deb-build: deb-clean deb-make
	package/debian/copy_debian.sh
	docker run -v $(shell pwd)/package/debian:/app $(DOCKER_NAME) /app/debuild.sh

deb-contents:
	docker run -v $(shell pwd)/package/debian:/app $(DOCKER_NAME) /app/contents.sh

deb-env-make:
	docker run -v $(shell pwd)/package/debian:/app $(DOCKER_NAME) /app/debmake.sh virtualenv

deb-env-build: deb-clean deb-env-make
	package/debian/copy_debian.sh virtualenv
	docker run -v $(shell pwd)/package/debian:/app $(DOCKER_NAME) /app/debuild.sh virtualenv

deb-clean:
	rm -rf package/debian/build

# For AUR: https://wiki.archlinux.org/index.php/Python_package_guidelines
#  and: https://wiki.archlinux.org/index.php/Creating_packages
arch-update:
	cd package/archlinux
	makepkg --printsrcinfo > .SRCINFO

arch-install: arch-update
	cd package/archlinux
	makepkg -si

arch-build: arch-update
	cd package/archlinux
	makepkg

arch-upload: arch-update
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

arch-clean:
	cd package/archlinux
	rm -rf pkg src *.tar*

launch:
	./launch.sh

clean: arch-clean deb-clean python-clean
