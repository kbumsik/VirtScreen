# VirtScreen
> Make your iPad/tablet/computer as a secondary monitor on Linux.

![gif example](https://github.com/kbumsik/VirtScreen/blob/d2387d3321bd4d110d890ca87703196df203dc89/icon/gif_example.gif?raw=true)

VirtScreen is an easy-to-use Linux GUI app that creates a virtual secondary screen and shares it through VNC.

VirtScreen is based on [PyQt5](https://www.riverbankcomputing.com/software/pyqt/intro) and [Twisted](https://twistedmatrix.com) in Python side and uses [x11vnc](https://github.com/LibVNC/x11vnc) and XRandR.

## Installation & running

### Installing dependancies

You need [`x11vnc`](https://github.com/LibVNC/x11vnc) and `xrandr`. To install (example on Ubuntu):
```bash
$ sudo apt-get install x11vnc
```

### Installing package

#### From the Git repository

```bash
$ python setup.py install # add --user option if you have permission problem
```


### How to run

Simply run `virtscreen` after installation:

```bash
$ virtscreen
```

If you want to run it directly from the Git repository:

```bash
$ ./launch.sh
```

Note that any files related to VirtScreen, including password and log, will be stored in `~/.virtscreen` directory.
