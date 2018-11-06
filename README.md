<h1 align="center">
  <img src="data/icon_full.svg" width="21%">
  <br/>
  VirtScreen
</h1>

<h4 align="center">
  Make your iPad/tablet/computer as a secondary monitor on Linux.
</h4>

<div align="center">
  <a href="https://github.com/kbumsik/VirtScreen">
    <img src="https://raw.githubusercontent.com/kbumsik/VirtScreen/master/data/gif_example.gif" alt="VirtScreen" width="80%">
  </a>
</div>

## Description

VirtScreen is an easy-to-use Linux GUI app that creates a virtual secondary screen and shares it through VNC.

VirtScreen is based on [PyQt5](https://www.riverbankcomputing.com/software/pyqt/intro) and [asyncio](https://docs.python.org/3/library/asyncio.html) in Python side and uses [x11vnc](https://github.com/LibVNC/x11vnc) and XRandR.

## Features

* No more typing commands - create a second VNC screen with a few clicks from the GUI.
* ...But there is also command-line only options for CLI lovers.
* Highly configurable - resolutions, portrait mode, and HiDPI mode.
* Works on any Linux Distro with Xorg
* Lightweight
* System Tray Icon

## How to use

1. Run the app.
2. Set options (resolution etc.) and enable the virtual screen.
3. Go to VNC tab and then start the VNC server.
4. Run your favorite VNC client app on your second device and connect it to the IP address appeared on the app.

### CLI-only option

You can run VirtScreen with `virtscreen` (or `./VirtScreen.AppImage` if you use the AppImage package) with additional arguments.

```bash
usage: virtscreen [-h] [--auto] [--left] [--right] [--above] [--below]
                  [--portrait] [--hidpi]

Make your iPad/tablet/computer as a secondary monitor on Linux.

You can start VirtScreen in the following two modes:

 - GUI mode: A system tray icon will appear when no argument passed.
          You need to use this first to configure a virtual screen.
 - CLI mode: After configured the virtual screen, you can start VirtScreen
          in CLI mode if you do not want a GUI, by passing any arguments

optional arguments:
  -h, --help       show this help message and exit
  --auto           create a virtual screen automatically using previous
                   settings (from both GUI mode and CLI mode)
  --left           a virtual screen will be created left to the primary
                   monitor
  --right          right to the primary monitor
  --above, --up    above the primary monitor
  --below, --down  below the primary monitor
  --portrait       Portrait mode. Width and height of the screen are swapped
  --hidpi          HiDPI mode. Width and height are doubled

example:
virtscreen  # GUI mode. You need to use this first
            # to configure the screen
virtscreen --auto       # CLI mode. Scrren will be created using previous
                        #   settings (from both GUI mode and CLI mode)
virtscreen --left    # CLI mode. On the left to the primary monitor
virtscreen --below   # CLI mode. Below the primary monitor.
virtscreen --below --portrait           # Below, and portrait mode.
virtscreen --below --portrait  --hipdi  # Below, portrait, HiDPI mode.
```

## Installation

### Universal package (AppImage)

Download a `.AppImage` package from [releases page](https://github.com/kbumsik/VirtScreen/releases). Then make it executable:

```shell
chmod a+x VirtScreen.AppImage
```

Then you can run it by double click the file or `./VirtScreen.AppImage` in terminal.

### Debian (Ubuntu)

Download a `.deb` package from [releases page](https://github.com/kbumsik/VirtScreen/releases). Then install it:

```shell
sudo apt-get update
sudo apt-get install x11vnc
sudo dpkg -i virtscreen.deb
rm virtscreen.deb
```

### Arch Linux (AUR)

There is [`virtscreen` AUR package](https://aur.archlinux.org/packages/virtscreen/) available. Though there are many ways to install the AUR package, one of the easiest way is to use [`yaourt`](https://github.com/polygamma/aurman) AUR helper:

```bash
yaourt virtscreen
```

### Python `pip`

Although not recommended, you may install it using `pip`. In this case, you need to install the dependancy (`xrandr` and `x11vnc`) manually.

```bash
sudo pip install virtscreen
```
