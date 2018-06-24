#!/usr/bin/python3

# Python standard packages
import sys
import os
import subprocess
import signal
import re
import atexit
import time
import json
import shutil
import argparse
from pathlib import Path
from enum import Enum
from typing import List, Dict, Callable

# Import OpenGL library for Nvidia driver
# https://github.com/Ultimaker/Cura/pull/131#issuecomment-176088664
import ctypes
from ctypes.util import find_library
ctypes.CDLL(find_library('GL'), ctypes.RTLD_GLOBAL)

# PyQt5 packages
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QObject, QUrl, Qt, pyqtProperty, pyqtSlot, pyqtSignal, Q_ENUMS
from PyQt5.QtGui import QIcon, QCursor
from PyQt5.QtQml import qmlRegisterType, QQmlApplicationEngine, QQmlListProperty
# Twisted and netifaces
from twisted.internet import protocol, error
from netifaces import interfaces, ifaddresses, AF_INET

# -------------------------------------------------------------------------------
# file path definitions
# -------------------------------------------------------------------------------
# Sanitize environment variables
# https://wiki.sei.cmu.edu/confluence/display/c/ENV03-C.+Sanitize+the+environment+when+invoking+external+programs

# Delete $HOME env for security reason. This will make
# Path.home() to look up in the password directory (pwd module)
if 'HOME' in os.environ:
    del os.environ['HOME']
os.environ['HOME'] = str(Path.home())
os.environ['PATH'] = os.confstr("CS_PATH")  # Sanitize $PATH

# Setting home path and base path
# https://www.freedesktop.org/software/systemd/man/file-hierarchy.html
# HOME_PATH will point to ~/.config/virtscreen by default
if 'XDG_CONFIG_HOME' in os.environ and os.environ['XDG_CONFIG_HOME']:
    HOME_PATH = os.environ['XDG_CONFIG_HOME']
else:
    HOME_PATH = os.environ['HOME']
    if HOME_PATH is not None:
        HOME_PATH = HOME_PATH + "/.config"
if HOME_PATH is not None:
    HOME_PATH = HOME_PATH + "/virtscreen"
BASE_PATH = os.path.dirname(__file__)
# Path in ~/.virtscreen
X11VNC_LOG_PATH = HOME_PATH + "/x11vnc_log.txt"
X11VNC_PASSWORD_PATH = HOME_PATH + "/x11vnc_passwd"
CONFIG_PATH = HOME_PATH + "/config.json"
# Path in the program path
ICON_PATH = BASE_PATH + "/icon/icon.png"
ASSETS_PATH = BASE_PATH + "/assets"
DATA_PATH = ASSETS_PATH + "/data.json"
DEFAULT_CONFIG_PATH = ASSETS_PATH + "/config.default.json"
MAIN_QML_PATH = ASSETS_PATH + "/main.qml"


# -------------------------------------------------------------------------------
# Subprocess wrapper
# -------------------------------------------------------------------------------
class SubprocessWrapper:
    def __init__(self):
        pass

    def check_output(self, arg) -> None:
        return subprocess.check_output(arg.split(), stderr=subprocess.STDOUT).decode('utf-8')

    def run(self, arg: str, input: str = None, check=False) -> str:
        if input:
            input = input.encode('utf-8')
        return subprocess.run(arg.split(), input=input, stdout=subprocess.PIPE,
                              check=check, stderr=subprocess.STDOUT).stdout.decode('utf-8')


# -------------------------------------------------------------------------------
# Twisted class
# -------------------------------------------------------------------------------
class ProcessProtocol(protocol.ProcessProtocol):
    def __init__(self, onConnected, onOutReceived, onErrRecevied, onProcessEnded, logfile=None):
        self.onConnected = onConnected
        self.onOutReceived = onOutReceived
        self.onErrRecevied = onErrRecevied
        self.onProcessEnded = onProcessEnded
        self.logfile = logfile
        # We cannot import this at the top of the file because qt5reactor should
        # be installed in the main function first.
        from twisted.internet import reactor  # pylint: disable=E0401
        self.reactor = reactor

    def run(self, arg: str):
        """Spawn a process
        
        Arguments:
            arg {str} -- arguments in string
        """

        args = arg.split()
        self.reactor.spawnProcess(self, args[0], args=args, env=os.environ)

    def kill(self):
        """Kill a spawned process
        """
        self.transport.signalProcess('INT')

    def connectionMade(self):
        print("connectionMade!")
        self.onConnected()
        self.transport.closeStdin()  # No more input

    def outReceived(self, data):
        # print("outReceived! with %d bytes!" % len(data))
        self.onOutReceived(data)
        if self.logfile is not None:
            self.logfile.write(data)

    def errReceived(self, data):
        # print("errReceived! with %d bytes!" % len(data))
        self.onErrRecevied(data)
        if self.logfile is not None:
            self.logfile.write(data)

    def inConnectionLost(self):
        print("inConnectionLost! stdin is closed! (we probably did it)")
        pass

    def outConnectionLost(self):
        print("outConnectionLost! The child closed their stdout!")
        pass

    def errConnectionLost(self):
        print("errConnectionLost! The child closed their stderr.")
        pass

    def processExited(self, reason):
        exitCode = reason.value.exitCode
        if exitCode is None:
            print("Unknown exit")
            return
        print("processEnded, status", exitCode)

    def processEnded(self, reason):
        if self.logfile is not None:
            self.logfile.close()
        exitCode = reason.value.exitCode
        if exitCode is None:
            print("Unknown exit")
            self.onProcessEnded(1)
            return
        print("processEnded, status", exitCode)
        print("quitting")
        self.onProcessEnded(exitCode)


# -------------------------------------------------------------------------------
# Display properties
# -------------------------------------------------------------------------------
class Display(object):
    __slots__ = ['name', 'primary', 'connected', 'active', 'width', 'height', 'x_offset', 'y_offset']

    def __init__(self):
        self.name: str = None
        self.primary: bool = False
        self.connected: bool = False
        self.active: bool = False
        self.width: int = 0
        self.height: int = 0
        self.x_offset: int = 0
        self.y_offset: int = 0

    def __str__(self):
        ret = f"{self.name}"
        if self.connected:
            ret += " connected"
        else:
            ret += " disconnected"
        if self.primary:
            ret += " primary"
        if self.active:
            ret += f" {self.width}x{self.height}+{self.x_offset}+{self.y_offset}"
        else:
            ret += f" not active {self.width}x{self.height}"
        return ret


class DisplayProperty(QObject):
    def __init__(self, display: Display, parent=None):
        super(DisplayProperty, self).__init__(parent)
        self._display = display

    @property
    def display(self):
        return self._display

    @pyqtProperty(str, constant=True)
    def name(self):
        return self._display.name

    @name.setter
    def name(self, name):
        self._display.name = name

    @pyqtProperty(bool, constant=True)
    def primary(self):
        return self._display.primary

    @primary.setter
    def primary(self, primary):
        self._display.primary = primary

    @pyqtProperty(bool, constant=True)
    def connected(self):
        return self._display.connected

    @connected.setter
    def connected(self, connected):
        self._display.connected = connected

    @pyqtProperty(bool, constant=True)
    def active(self):
        return self._display.active

    @active.setter
    def active(self, active):
        self._display.active = active

    @pyqtProperty(int, constant=True)
    def width(self):
        return self._display.width

    @width.setter
    def width(self, width):
        self._display.width = width

    @pyqtProperty(int, constant=True)
    def height(self):
        return self._display.height

    @height.setter
    def height(self, height):
        self._display.height = height

    @pyqtProperty(int, constant=True)
    def x_offset(self):
        return self._display.x_offset

    @x_offset.setter
    def x_offset(self, x_offset):
        self._display.x_offset = x_offset

    @pyqtProperty(int, constant=True)
    def y_offset(self):
        return self._display.y_offset

    @y_offset.setter
    def y_offset(self, y_offset):
        self._display.y_offset = y_offset


# -------------------------------------------------------------------------------
# Screen adjustment class
# -------------------------------------------------------------------------------
class XRandR(SubprocessWrapper):
    VIRT_SCREEN_SUFFIX = "_virt"

    def __init__(self):
        super(XRandR, self).__init__()
        self.mode_name: str
        self.screens: List[Display] = []
        self.virt: Display() = None
        self.primary: Display() = None
        self.virt_name: str = ''
        self.virt_idx: int = None
        self.primary_idx: int = None
        # Primary display
        self._update_screens()

    def _update_screens(self) -> None:
        output = self.run("xrandr")
        self.primary = None
        self.virt = None
        self.screens = []
        self.virt_idx = None
        self.primary_idx = None
        pattern = re.compile(r"^(\S*)\s+(connected|disconnected)\s+((primary)\s+)?"
                             r"((\d+)x(\d+)\+(\d+)\+(\d+)\s+)?.*$", re.M)
        for idx, match in enumerate(pattern.finditer(output)):
            screen = Display()
            screen.name = match.group(1)
            if self.virt_name and screen.name == self.virt_name:
                self.virt_idx = idx
            screen.primary = True if match.group(4) else False
            if screen.primary:
                self.primary_idx = idx
            screen.connected = True if match.group(2) == "connected" else False
            screen.active = True if match.group(5) else False
            self.screens.append(screen)
            if not screen.active:
                continue
            screen.width = int(match.group(6))
            screen.height = int(match.group(7))
            screen.x_offset = int(match.group(8))
            screen.y_offset = int(match.group(9))
        print("Display information:")
        for s in self.screens:
            print("\t", s)
        if self.primary_idx is None:
            raise RuntimeError("There is no primary screen detected.\n"
                               "Go to display settings and set\n"
                               "a primary screen\n")
        if self.virt_idx == self.primary_idx:
            raise RuntimeError("Virtual screen must be selected other than the primary screen")
        if self.virt_idx is not None:
            self.virt = self.screens[self.virt_idx]
        elif self.virt_name and self.virt_idx is None:
            raise RuntimeError("No virtual screen name found")
        self.primary = self.screens[self.primary_idx]

    def _add_screen_mode(self, width, height, portrait, hidpi) -> None:
        if not self.virt or not self.virt_name:
            raise RuntimeError("No virtual screen selected.\n"
                               "Go to Display->Virtual Display->Advaced\n"
                               "To select a device.")
        # Set virtual screen property first
        self.virt.width = width
        self.virt.height = height
        if portrait:
            self.virt.width = height
            self.virt.height = width
        if hidpi:
            self.virt.width *= 2
            self.virt.height *= 2
        self.mode_name = str(self.virt.width) + "x" + str(self.virt.height) + self.VIRT_SCREEN_SUFFIX
        # Then create using xrandr command
        args_addmode = f"xrandr --addmode {self.virt.name} {self.mode_name}"
        try:
            self.check_output(args_addmode)
        except subprocess.CalledProcessError:
            # When failed create mode and then add again
            output = self.run(f"cvt {self.virt.width} {self.virt.height}")
            mode = re.search(r"^.*Modeline\s*\".*\"\s*(.*)$", output, re.M).group(1)
            # Create new screen mode
            self.check_output(f"xrandr --newmode {self.mode_name} {mode}")
            # Add mode again
            self.check_output(args_addmode)
        # After adding mode the program should delete the mode automatically on exit
        atexit.register(self.delete_virtual_screen)

    def get_primary_screen(self) -> Display:
        self._update_screens()
        return self.primary

    def get_virtual_screen(self) -> Display:
        self._update_screens()
        return self.virt

    def create_virtual_screen(self, width, height, portrait=False, hidpi=False, pos='') -> None:
        self._update_screens()
        print("creating: ", self.virt)
        self._add_screen_mode(width, height, portrait, hidpi)
        arg_pos = ['left', 'right', 'above', 'below']
        xrandr_pos = ['--left-of', '--right-of', '--above', '--below']
        if pos and pos in arg_pos:
            # convert pos for xrandr
            pos = xrandr_pos[arg_pos.index(pos)]
            pos += ' ' + self.primary.name
        elif not pos:
            pos = '--preferred'
        else:
            raise RuntimeError("Incorrect position option selected.")
        self.check_output(f"xrandr --output {self.virt.name} --mode {self.mode_name}")
        self.check_output("sleep 5")
        self.check_output(f"xrandr --output {self.virt.name} {pos}")
        self._update_screens()

    def delete_virtual_screen(self) -> None:
        self._update_screens()
        try:
            self.virt.name
            self.mode_name
        except AttributeError:
            return
        self.run(f"xrandr --output {self.virt.name} --off")
        self.run(f"xrandr --delmode {self.virt.name} {self.mode_name}")
        atexit.unregister(self.delete_virtual_screen)
        self._update_screens()


# -------------------------------------------------------------------------------
# QML Backend class
# -------------------------------------------------------------------------------
class Backend(QObject):
    """ Backend class for QML frontend """

    class VNCState:
        """ Enum to indicate a state of the VNC server """
        OFF = 0
        ERROR = 1
        WAITING = 2
        CONNECTED = 3

    Q_ENUMS(VNCState)

    # Signals
    onVirtScreenCreatedChanged = pyqtSignal(bool)
    onVncUsePasswordChanged = pyqtSignal(bool)
    onVncStateChanged = pyqtSignal(VNCState)
    onDisplaySettingClosed = pyqtSignal()
    onError = pyqtSignal(str)

    def __init__(self, parent=None):
        super(Backend, self).__init__(parent)
        # Virtual screen properties
        self.xrandr: XRandR = XRandR()
        self._virtScreenCreated: bool = False
        # VNC server properties
        self._vncUsePassword: bool = False
        self._vncState: self.VNCState = self.VNCState.OFF
        # Primary screen and mouse posistion
        self.vncServer: ProcessProtocol
        # Check config file 
        # and initialize if needed
        need_init = False
        if not os.path.exists(CONFIG_PATH):
            shutil.copy(DEFAULT_CONFIG_PATH, CONFIG_PATH)
            need_init = True
        # Version check
        file_match = True
        with open(CONFIG_PATH, 'r') as f_config, open(DATA_PATH, 'r') as f_data:
            config = json.load(f_config)
            data = json.load(f_data)
            if config['version'] != data['version']:
                file_match = False
        # Override config with default when version doesn't match
        if not file_match:
            shutil.copy(DEFAULT_CONFIG_PATH, CONFIG_PATH)
            need_init = True
        # initialize config file
        if need_init:
            # 1. Available x11vnc options
            # Get available x11vnc options from x11vnc first
            p = SubprocessWrapper()
            arg = 'x11vnc -opts'
            ret = p.run(arg)
            options = tuple(m.group(1) for m in re.finditer("\s*(-\w+)\s+", ret))
            # Set/unset available x11vnc options flags in config
            with open(CONFIG_PATH, 'r') as f, open(DATA_PATH, 'r') as f_data:
                config = json.load(f)
                data = json.load(f_data)
                for key, value in config["x11vncOptions"].items():
                    if key in options:
                        value["available"] = True
                    else:
                        value["available"] = False
                # Default Display settings app for a Desktop Environment
                desktop_environ = os.environ['XDG_CURRENT_DESKTOP'].lower()
                for key, value in data['displaySettingApps'].items():
                    for de in value['XDG_CURRENT_DESKTOP']:
                        if de in desktop_environ:
                            config["displaySettingApp"] = key
            # Save the new config
            with open(CONFIG_PATH, 'w') as f:
                f.write(json.dumps(config, indent=4, sort_keys=True))

    # Qt properties
    @pyqtProperty(str, constant=True)
    def settings(self):
        with open(CONFIG_PATH, "r") as f:
            return f.read()

    @settings.setter
    def settings(self, json_str):
        with open(CONFIG_PATH, "w") as f:
            f.write(json_str)

    @pyqtProperty(bool, notify=onVirtScreenCreatedChanged)
    def virtScreenCreated(self):
        return self._virtScreenCreated

    @virtScreenCreated.setter
    def virtScreenCreated(self, value):
        self._virtScreenCreated = value
        self.onVirtScreenCreatedChanged.emit(value)

    @pyqtProperty(QQmlListProperty, constant=True)
    def screens(self):
        try:
            return QQmlListProperty(DisplayProperty, self, [DisplayProperty(x) for x in self.xrandr.screens])
        except RuntimeError as e:
            self.onError.emit(str(e))
            return QQmlListProperty(DisplayProperty, self, [])

    @pyqtProperty(bool, notify=onVncUsePasswordChanged)
    def vncUsePassword(self):
        if os.path.isfile(X11VNC_PASSWORD_PATH):
            self._vncUsePassword = True
        else:
            if self._vncUsePassword:
                self.vncUsePassword = False
        return self._vncUsePassword

    @vncUsePassword.setter
    def vncUsePassword(self, use):
        self._vncUsePassword = use
        self.onVncUsePasswordChanged.emit(use)

    @pyqtProperty(VNCState, notify=onVncStateChanged)
    def vncState(self):
        return self._vncState

    @vncState.setter
    def vncState(self, state):
        self._vncState = state
        self.onVncStateChanged.emit(self._vncState)

    # Qt Slots
    @pyqtSlot(str, int, int, bool, bool)
    def createVirtScreen(self, device, width, height, portrait, hidpi, pos=''):
        self.xrandr.virt_name = device
        print("Creating a Virtual Screen...")
        try:
            self.xrandr.create_virtual_screen(width, height, portrait, hidpi, pos)
        except subprocess.CalledProcessError as e:
            self.onError.emit(str(e.cmd) + '\n' + e.stdout.decode('utf-8'))
            return
        except RuntimeError as e:
            self.onError.emit(str(e))
            return
        self.virtScreenCreated = True

    @pyqtSlot()
    def deleteVirtScreen(self):
        print("Deleting the Virtual Screen...")
        if self.vncState is not self.VNCState.OFF:
            self.onError.emit("Turn off the VNC server first")
            self.virtScreenCreated = True
            return
        try:
            self.xrandr.delete_virtual_screen()
        except RuntimeError as e:
            self.onError.emit(str(e))
            return
        self.virtScreenCreated = False

    @pyqtSlot(str)
    def createVNCPassword(self, password):
        if password:
            password += '\n' + password + '\n\n'  # verify + confirm
            p = SubprocessWrapper()
            try:
                p.run(f"x11vnc -storepasswd {X11VNC_PASSWORD_PATH}", input=password, check=True)
            except subprocess.CalledProcessError as e:
                self.onError.emit(str(e.cmd) + '\n' + e.stdout.decode('utf-8'))
                return
            self.vncUsePassword = True
        else:
            self.onError.emit("Empty password")

    @pyqtSlot()
    def deleteVNCPassword(self):
        if os.path.isfile(X11VNC_PASSWORD_PATH):
            os.remove(X11VNC_PASSWORD_PATH)
            self.vncUsePassword = False
        else:
            self.onError.emit("Failed deleting the password file")

    @pyqtSlot(int)
    def startVNC(self, port):
        # Check if a virtual screen created
        if not self.virtScreenCreated:
            self.onError.emit("Virtual Screen not crated.")
            return
        if self.vncState is not self.VNCState.OFF:
            self.onError.emit("VNC Server is already running.")
            return
        # regex used in callbacks
        patter_connected = re.compile(r"^.*Got connection from client.*$", re.M)
        patter_disconnected = re.compile(r"^.*client_count: 0*$", re.M)

        # define callbacks
        def _onConnected():
            print("VNC started.")
            self.vncState = self.VNCState.WAITING

        def _onReceived(data):
            data = data.decode("utf-8")
            if (self._vncState is not self.VNCState.CONNECTED) and patter_connected.search(data):
                print("VNC connected.")
                self.vncState = self.VNCState.CONNECTED
            if (self._vncState is self.VNCState.CONNECTED) and patter_disconnected.search(data):
                print("VNC disconnected.")
                self.vncState = self.VNCState.WAITING

        def _onEnded(exitCode):
            if exitCode is not 0:
                self.vncState = self.VNCState.ERROR
                self.onError.emit('X11VNC: Error occurred.\n'
                                  'Double check if the port is already used.')
                self.vncState = self.VNCState.OFF  # TODO: better handling error state
            else:
                self.vncState = self.VNCState.OFF
            print("VNC Exited.")
            atexit.unregister(self.stopVNC)
        # load settings
        with open(CONFIG_PATH, 'r') as f:
            config = json.load(f)
        options = ''
        if config['customX11vncArgs']['enabled']:
            options = config['customX11vncArgs']['value']
        else:
            for key, value in config['x11vncOptions'].items():
                if value['available'] and value['enabled']:
                    options += key + ' '
                    if value['arg'] is not None:
                        options += str(value['arg']) + ' '
        # Sart x11vnc, turn settings object into VNC arguments format
        logfile = open(X11VNC_LOG_PATH, "wb")
        self.vncServer = ProcessProtocol(_onConnected, _onReceived, _onReceived, _onEnded, logfile)
        try:
            virt = self.xrandr.get_virtual_screen()
        except RuntimeError as e:
            self.onError.emit(str(e))
            return
        clip = f"{virt.width}x{virt.height}+{virt.x_offset}+{virt.y_offset}"
        arg = f"x11vnc -rfbport {port} -clip {clip} {options}"
        if self.vncUsePassword:
            arg += f" -rfbauth {X11VNC_PASSWORD_PATH}"
        self.vncServer.run(arg)
        # auto stop on exit
        atexit.register(self.stopVNC, force=True)

    @pyqtSlot(str)
    def openDisplaySetting(self, app: str = "arandr"):
        # define callbacks
        def _onConnected():
            print("External Display Setting opened.")

        def _onReceived(data):
            pass

        def _onEnded(exitCode):
            print("External Display Setting closed.")
            self.onDisplaySettingClosed.emit()
            if exitCode is not 0:
                self.onError.emit(f'Error opening "{running_program}".')
        with open(DATA_PATH, 'r') as f:
            data = json.load(f)['displaySettingApps']
            if app not in data:
                self.onError.emit('Wrong display settings program')
                return
        program_list = [data[app]['args'], "arandr"]
        program = ProcessProtocol(_onConnected, _onReceived, _onReceived, _onEnded, None)
        running_program = ''
        for arg in program_list:
            if not shutil.which(arg.split()[0]):
                continue
            running_program = arg
            program.run(arg)
            return
        self.onError.emit('Failed to find a display settings program.\n'
                          'Please install ARandR package.\n'
                          '(e.g. sudo apt-get install arandr)\n'
                          'Please issue a feature request\n'
                          'if you wish to add a display settings\n'
                          'program for your Desktop Environment.')

    @pyqtSlot()
    def stopVNC(self, force=False):
        if force:
            # Usually called from atexit().
            self.vncServer.kill()
            time.sleep(3)  # Make sure X11VNC shutdown before execute next atexit().
        if self._vncState in (self.VNCState.WAITING, self.VNCState.CONNECTED):
            self.vncServer.kill()
        else:
            self.onError.emit("stopVNC called while it is not running")

    @pyqtSlot()
    def clearCache(self):
        engine.clearComponentCache()

    @pyqtSlot()
    def quitProgram(self):
        self.blockSignals(True)  # This will prevent invoking auto-restart or etc.
        QApplication.instance().quit()


class Cursor(QObject):
    """ Global mouse cursor position """

    def __init__(self, parent=None):
        super(Cursor, self).__init__(parent)

    @pyqtProperty(int)
    def x(self):
        cursor = QCursor().pos()
        return cursor.x()

    @pyqtProperty(int)
    def y(self):
        cursor = QCursor().pos()
        return cursor.y()


class Network(QObject):
    """ Backend class for network interfaces """
    onIPAddressesChanged = pyqtSignal()

    def __init__(self, parent=None):
        super(Network, self).__init__(parent)

    @pyqtProperty('QStringList', notify=onIPAddressesChanged)
    def ipAddresses(self):
        for interface in interfaces():
            if interface == 'lo':
                continue
            addresses = ifaddresses(interface).get(AF_INET, None)
            if addresses is None:
                continue
            for link in addresses:
                if link is not None:
                    yield link['addr']
                    

# -------------------------------------------------------------------------------
# Main Code
# -------------------------------------------------------------------------------
def main() -> None:
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
    if os.environ['XDG_SESSION_TYPE'].lower() == 'wayland':
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
    
    # Check environment first
    from PyQt5.QtWidgets import QMessageBox, QSystemTrayIcon
    def dialog(message: str) -> None:
        QMessageBox.critical(None, "VirtScreen", message)
    if not QSystemTrayIcon.isSystemTrayAvailable():
        dialog("Cannot detect system tray on this system.")
        sys.exit(1)
    check_env(dialog)
    
    # Replace Twisted reactor with qt5reactor
    import qt5reactor  # pylint: disable=E0401
    qt5reactor.install()
    from twisted.internet import reactor  # pylint: disable=E0401

    app.setWindowIcon(QIcon(ICON_PATH))
    os.environ["QT_QUICK_CONTROLS_STYLE"] = "Material"
    # os.environ["QT_QUICK_CONTROLS_STYLE"] = "Fusion"

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
    reactor.run()

def main_cli(args: argparse.Namespace):
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
    from twisted.internet import reactor  # pylint: disable=E0401
    backend.startVNC(config['vnc']['port'])
    reactor.run()

if __name__ == '__main__':
    main()
