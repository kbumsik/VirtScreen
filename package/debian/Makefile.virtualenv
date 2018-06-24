prefix = /usr

all:
	: # do nothing

SHELL = /bin/bash
install:
	# Create virtualenv
	install -d $(DESTDIR)$(prefix)/share/virtscreen
	source $(HOME)/miniconda/bin/activate && \
		conda create -y --copy --prefix $(DESTDIR)$(prefix)/share/virtscreen/env python=3.6
	# Install VirtScreen using pip
	source $(HOME)/miniconda/bin/activate && \
		source activate $(DESTDIR)$(prefix)/share/virtscreen/env && \
		pip install .
	# Fix hashbang and move executable
	sed -i "1s:.*:#!$(prefix)/share/virtscreen/env/bin/python3:" \
			$(DESTDIR)$(prefix)/share/virtscreen/env/bin/virtscreen
	install -D launch_env.sh \
			$(DESTDIR)$(prefix)/bin/virtscreen
	# Delete unnecessary installed files done by setup.py
	rm -rf $(DESTDIR)$(prefix)/share/virtscreen/env/lib/python3.6/site-packages/usr
	# Copy desktop entry and icon
	install -m 644 -D virtscreen.desktop \
			$(DESTDIR)$(prefix)/share/applications/virtscreen.desktop
	install -m 644 -D data/virtscreen.png \
			$(DESTDIR)$(prefix)/share/pixmaps/virtscreen.png

clean:
	: # do nothing

distclean: clean

uninstall:
	: # do nothing

# override_dh_usrlocal:
#     : # do nothing

.PHONY: all install clean distclean uninstall
