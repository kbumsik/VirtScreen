# See https://packaging.python.org/tutorials/distributing-packages/#packaging-your-project
# for python packaging reference.

.PHONY:

python-wheel:
	python setup.py bdist_wheel --universal

python-install:
	python setup.py install --user

pip-upload: python-wheel
	twine upload dist/*

.ONESHELL:

# For Debian packaging, https://www.debian.org/doc/manuals/debmake-doc/ch08.en.html#setup-py
deb-docker-build:
	docker build -f package/debian/Dockerfile -t debmake .

deb-docker:
	docker run --privileged --interactive --tty -v $(shell pwd)/package/debian:/app debmake /bin/bash
	
deb-docker-rm:
	docker image rm -f debmake

deb-make:
	docker run --privileged --interactive --tty --rm -v $(shell pwd)/package/debian:/app debmake /app/debmake.sh

deb-build:
	docker run --privileged --interactive --tty --rm -v $(shell pwd)/package/debian:/app debmake /app/debuild.sh

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

clean: arch-clean deb-clean
	rm -rf build dist virtscreen.egg-info virtscreen/qml/*.qmlc
