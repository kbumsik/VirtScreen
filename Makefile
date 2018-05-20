# See https://packaging.python.org/tutorials/distributing-packages/#packaging-your-project
# for python packaging reference.

.PHONY: wheel install clean

wheel:
	python setup.py bdist_wheel --universal

upload:
	twine upload dist/*

install:
	python setup.py install --user

launch:
	./launch.sh

clean:
	rm -rf build dist virtscreen.egg-info
