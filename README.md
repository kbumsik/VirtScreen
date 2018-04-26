# VirtScreen
> Make your iPad/tablet/computer as a secondary monitor on Linux.

VirtScreen is an easy-to-use Linux GUI app that creates a virtual secondary screen and shares it through VNC.

VirtScreen is based on [PyQt5](https://www.riverbankcomputing.com/software/pyqt/intro) and [Twisted](https://twistedmatrix.com) in Python side and uses [x11vnc](https://github.com/LibVNC/x11vnc) and XRandR.

## Dependency

1. You need [`x11vnc`](https://github.com/LibVNC/x11vnc) and `xrandr`. To install (example on Ubuntu):
```bash
sudo apt-get install x11vnc xrandr
```

2. Install Python dependencies:

```
pip install -r requirements.txt
```

## How to run

Simply run this in the project root:

```bash
./virtscreen.py

or

python virtscreen.py
```

Note that any files related to VirtScreen, including password and log, will be stored in `~/.virtscreen` directory.
