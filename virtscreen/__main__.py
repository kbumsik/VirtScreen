#!/usr/bin/python3

# Python standard packages
import sys
import os
import signal
import json
import shutil
import argparse
from typing import Callable
import asyncio

# Import OpenGL library for Nvidia driver
# https://github.com/Ultimaker/Cura/pull/131#issuecomment-176088664
import ctypes
from ctypes.util import find_library
ctypes.CDLL(find_library('GL'), ctypes.RTLD_GLOBAL)

from PyQt5.QtWidgets import QApplication
from PyQt5.QtQml import qmlRegisterType, QQmlApplicationEngine
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QUrl
from quamash import QEventLoop

from .display import DisplayProperty
from .xrandr import XRandR
from .qt_backend import Backend, Cursor, Network
from .path import HOME_PATH, ICON_PATH, MAIN_QML_PATH, CONFIG_PATH


def main() -> None:
    """Start main program"""
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        description='Make your iPad/tablet/computer as a secondary monitor on Linux.\n\n'
                    'You can start VirtScreen in the following two modes:\n\n'
                    ' - GUI mode: A system tray icon will appear when no argument passed.\n'
                    '          You need to use this first to configure a virtual screen.\n'
                    ' - CLI mode: After configured the virtual screen, you can start VirtScreen\n'
                    '          in CLI mode if you do not want a GUI, by passing any arguments\n',
        epilog='example:\n'
               'virtscreen    # GUI mode. You need to use this first\n'
               '                to configure the screen\n'
               'virtscreen --auto    # CLI mode. Scrren will be created using previous\n'
               '                       settings (from both GUI mode and CLI mode)\n'
               'virtscreen --left    # CLI mode. On the left to the primary monitor\n'
               'virtscreen --below   # CLI mode. Below the primary monitor.\n'
               'virtscreen --below --portrait           # Below, and portrait mode.\n'
               'virtscreen --below --portrait  --hipdi  # Below, portrait, HiDPI mode.\n')
    parser.add_argument('--auto', action='store_true',
        help='create a virtual screen automatically using previous\n'
             'settings (from both GUI mode and CLI mode)')
    parser.add_argument('--left', action='store_true',
        help='a virtual screen will be created left to the primary\n'
             'monitor')
    parser.add_argument('--right', action='store_true',
        help='right to the primary monitor')
    parser.add_argument('--above', '--up', action='store_true',
        help='above the primary monitor')
    parser.add_argument('--below', '--down', action='store_true',
        help='below the primary monitor')
    parser.add_argument('--portrait', action='store_true',
        help='Portrait mode. Width and height of the screen are swapped')
    parser.add_argument('--hidpi', action='store_true',
        help='HiDPI mode. Width and height are doubled')
    # Add signal handler
    def on_exit(self, signum=None, frame=None):
        sys.exit(0)
    for sig in [signal.SIGINT, signal.SIGTERM, signal.SIGHUP, signal.SIGQUIT]:
        signal.signal(sig, on_exit)
    # Start main
    args = parser.parse_args()
    if any(vars(args).values()):
        main_cli(args)
    else:
        main_gui()
    print('Program should not reach here.')
    sys.exit(1)

def check_env(msg: Callable[[str], None]) -> None:
    """Check enveironments before start"""
    if os.environ.get('XDG_SESSION_TYPE', '').lower() == 'wayland':
        msg("Currently Wayland is not supported")
        sys.exit(1)
    if not HOME_PATH:
        msg("Cannot detect home directory.")
        sys.exit(1)
    if not os.path.exists(HOME_PATH):
        try:
            os.makedirs(HOME_PATH)
        except:
            msg("Cannot create ~/.config/virtscreen")
            sys.exit(1)
    if not shutil.which('x11vnc'):
        msg("x11vnc is not installed.")
        sys.exit(1)
    try:
        test = XRandR()
    except RuntimeError as e:
        msg(str(e))
        sys.exit(1)

def main_gui():
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    
    # Check environment first
    from PyQt5.QtWidgets import QMessageBox, QSystemTrayIcon
    def dialog(message: str) -> None:
        QMessageBox.critical(None, "VirtScreen", message)
    if not QSystemTrayIcon.isSystemTrayAvailable():
        dialog("Cannot detect system tray on this system.")
        sys.exit(1)
    check_env(dialog)
    
    app.setApplicationName("VirtScreen")
    app.setWindowIcon(QIcon(ICON_PATH))
    os.environ["QT_QUICK_CONTROLS_STYLE"] = "Material"

    # Register the Python type.  Its URI is 'People', it's v1.0 and the type
    # will be called 'Person' in QML.
    qmlRegisterType(DisplayProperty, 'VirtScreen.DisplayProperty', 1, 0, 'DisplayProperty')
    qmlRegisterType(Backend, 'VirtScreen.Backend', 1, 0, 'Backend')
    qmlRegisterType(Cursor, 'VirtScreen.Cursor', 1, 0, 'Cursor')
    qmlRegisterType(Network, 'VirtScreen.Network', 1, 0, 'Network')

    # Create a component factory and load the QML script.
    engine = QQmlApplicationEngine()
    engine.load(QUrl(MAIN_QML_PATH))
    if not engine.rootObjects():
        dialog("Failed to load QML")
        sys.exit(1)
    sys.exit(app.exec_())
    with loop:
        loop.run_forever()

def main_cli(args: argparse.Namespace):
    loop = asyncio.get_event_loop()
    for key, value in vars(args).items():
        print(key, ": ", value)
    # Check the environment
    check_env(print)
    if not os.path.exists(CONFIG_PATH):
        print("Configuration file does not exist.\n"
              "Configure a virtual screen using GUI first.")
        sys.exit(1)
    # By instantiating the backend, additional verifications of config
    # file will be done. 
    backend = Backend()
    # Get settings
    with open(CONFIG_PATH, 'r') as f:
        config = json.load(f)
    # Override settings from arguments
    position = ''
    if not args.auto:
        args_virt = ['portrait', 'hidpi']
        for prop in args_virt:
            if vars(args)[prop]:
                config['virt'][prop] = True
        args_position = ['left', 'right', 'above', 'below']
        tmp_args = {k: vars(args)[k] for k in args_position}
        if not any(tmp_args.values()):
            print("Choose a position relative to the primary monitor. (e.g. --left)")
            sys.exit(1)
        for key, value in tmp_args.items():
            if value:
                position = key
    # Create virtscreen and Start VNC
    def handle_error(msg):
        print('Error: ', msg)
        sys.exit(1)
    backend.onError.connect(handle_error)
    backend.createVirtScreen(config['virt']['device'], config['virt']['width'],
                        config['virt']['height'], config['virt']['portrait'],
                        config['virt']['hidpi'], position)
    def handle_vnc_changed(state):
        if state is backend.VNCState.OFF:
            sys.exit(0)
    backend.onVncStateChanged.connect(handle_vnc_changed)
    backend.startVNC(config['vnc']['port'])
    loop.run_forever()

if __name__ == '__main__':
    main()
