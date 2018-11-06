prefix = /usr

all:
	: # do nothing

SHELL = /bin/bash
install:
	mkdir -p $(DESTDIR)$(prefix)/bin
	install -m 755 VirtScreen.AppImage \
			$(DESTDIR)$(prefix)/bin/virtscreen
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
