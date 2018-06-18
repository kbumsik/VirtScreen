# See https://packaging.python.org/tutorials/distributing-packages/#packaging-your-project
# for python packaging reference.

DOCKER_NAME=kbumsik/virtscreen
DOCKER_RUN=docker run -v $(shell pwd)/package/debian:/app $(DOCKER_NAME)
DOCKER_RUN_TTY=docker run --interactive --tty -v $(shell pwd)/package/debian:/app $(DOCKER_NAME)

.PHONY:

python-wheel:
	python3 setup.py bdist_wheel --universal

python-install:
	pip3 install . --user

python-uninstall:
	pip3 uninstall virtscreen
	
python-clean:
	rm -rf build dist virtscreen.egg-info virtscreen/qml/*.qmlc

pip-upload: python-wheel
	twine upload dist/*

.ONESHELL:

# Docker
docker-build:
	docker build -f Dockerfile -t $(DOCKER_NAME) .

docker:
	$(DOCKER_RUN_TTY) /bin/bash
	
docker-rm:
	docker image rm -f $(DOCKER_NAME)

docker-pull:
	docker pull $(DOCKER_NAME)

docker-push:
	docker login
	docker push $(DOCKER_NAME)

# For Debian packaging, https://www.debian.org/doc/manuals/debmake-doc/ch08.en.html#setup-py
deb-make:
	$(DOCKER_RUN) /app/debmake.sh

deb-build: deb-make
	$(DOCKER_RUN) /app/copy_debian.sh
	$(DOCKER_RUN) /app/debuild.sh

deb-contents:
	$(DOCKER_RUN) /app/contents.sh

deb-env-make:
	$(DOCKER_RUN) /app/debmake.sh virtualenv

deb-env-build: deb-env-make
	$(DOCKER_RUN) /app/copy_debian.sh virtualenv
	$(DOCKER_RUN) /app/debuild.sh virtualenv

deb-chown:
	$(DOCKER_RUN) chown -R $(shell id -u):$(shell id -u) /app/build

deb-clean:
	$(DOCKER_RUN) rm -rf /app/build

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
