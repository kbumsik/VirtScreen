# VirtScreen

> Make your iPad/tablet/computer as a secondary monitor on Linux.

![gif example](https://raw.githubusercontent.com/kbumsik/VirtScreen/master/data/gif_example.gif)

VirtScreen is an easy-to-use Linux GUI app that creates a virtual secondary screen and shares it through VNC.

VirtScreen is based on [PyQt5](https://www.riverbankcomputing.com/software/pyqt/intro) and [Twisted](https://twistedmatrix.com) in Python side and uses [x11vnc](https://github.com/LibVNC/x11vnc) and XRandR.

## How to use

Upon installation (see Installing section to install), there will be a desktop entry called `VirtScreen`

![desktop entry](https://raw.githubusercontent.com/kbumsik/VirtScreen/master/data/desktop_entry.png)

Or you can run it using a command line:

```bash
$ virtscreen
```

## Installation

### Universal package (AppImage)

Download a `.AppImage` package from [releases page](https://github.com/kbumsik/VirtScreen/releases). Then make it executable:

```shell
chmod a+x VirtScreen-x86_64.AppImage
```

Then you can run it by double click the file or `./VirtScreen-x86_64.AppImage` in terminal.

### Debian (Ubuntu)

Download a `.deb` package from [releases page](https://github.com/kbumsik/VirtScreen/releases). Then install it:

```shell
sudo apt-get update
sudo apt-get install x11vnc
sudo dpkg -i virtscreen_0.2.4-1_all.deb 
rm virtscreen_0.2.4-1_all.deb
```

### Arch Linux (AUR)

There is [`virtscreen` AUR package](https://aur.archlinux.org/packages/virtscreen/) available. Though there are many ways to install the AUR package, one of the easiest way is to use [`yaourt`](https://github.com/polygamma/aurman) AUR helper:

```bash
yaourt virtscreen
```

### Python `pip`

Although not recommended, you may install it using `pip`. In this case, you need to install the dependancies manually.

You need [`x11vnc`](https://github.com/LibVNC/x11vnc), `xrandr`. To install (e.g. on Ubuntu):
```bash
sudo apt-get install x11vnc  # On Debian/Ubuntu, xrandr is included.
```

After you install the dependancies then run:

```bash
sudo pip install virtscreen
```
