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

clean: arch-clean
	rm -rf build dist virtscreen.egg-info
