# VirtScreen

> Make your iPad/tablet/computer as a secondary monitor on Linux.

![gif example](https://raw.githubusercontent.com/kbumsik/VirtScreen/master/data/gif_example.gif)

VirtScreen is an easy-to-use Linux GUI app that creates a virtual secondary screen and shares it through VNC.

VirtScreen is based on [PyQt5](https://www.riverbankcomputing.com/software/pyqt/intro) and [Twisted](https://twistedmatrix.com) in Python side and uses [x11vnc](https://github.com/LibVNC/x11vnc) and XRandR.

## How to use

Upon installation (see Installing section to install), there will be a desktop entry called `virtscreen`

![desktop entry](https://raw.githubusercontent.com/kbumsik/VirtScreen/master/data/desktop_entry.png)

Or you can run it using a command line:

```bash
$ virtscreen
```

## Installation

### Debian (Ubuntu)

A PPA package will be available soon.

### Arch Linux (AUR)

There is [`virtscreen` AUR package](https://aur.archlinux.org/packages/virtscreen/) available. Though there are many ways to install the AUR package, one of the easiest way is to use [`aurman`](https://github.com/polygamma/aurman) AUR helper:

```bash
$ aurman -S virtscreen
```

### Python `pip`

If your distro is none of above, you may install it using `pip`. In this case, you need to install the dependancies manually.

#### Dependancies

You need [`x11vnc`](https://github.com/LibVNC/x11vnc), `xrandr`, and PyQt5 libraries. To install (e.g. on Ubuntu):
```bash
$ sudo apt-get install x11vnc qtbase5-dev  # On Debian/Ubuntu, xrandr is included.
```

#### Installing

After you install the dependancies then run:

```bash
$ sudo pip install virtscreen
```
