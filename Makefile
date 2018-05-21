# See https://packaging.python.org/tutorials/distributing-packages/#packaging-your-project
# for python packaging reference.

.PHONY:

python-wheel:
	python setup.py bdist_wheel --universal

python-install:
	python setup.py install --user

pip-upload:
	twine upload dist/*

.ONESHELL:

arch-update:
	cd package/archlinux
	makepkg --printsrcinfo > .SRCINFO

arch-install: arch-update
	cd package/archlinux
	makepkg -si

arch-clean:
	cd package/archlinux
	rm -rf pkg src *.tar*

launch:
	./launch.sh

clean: arch-clean
	rm -rf build dist virtscreen.egg-info
