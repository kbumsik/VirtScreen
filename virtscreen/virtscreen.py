#!/usr/bin/env python

import sys, os, subprocess, signal, re, atexit, time, json, shutil
from pathlib import Path
from enum import Enum
from typing import List, Dict

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QObject, QUrl, Qt, pyqtProperty, pyqtSlot, pyqtSignal, Q_ENUMS
from PyQt5.QtGui import QIcon, QCursor
from PyQt5.QtQml import qmlRegisterType, QQmlApplicationEngine, QQmlListProperty

from twisted.internet import protocol, error
from netifaces import interfaces, ifaddresses, AF_INET

# -------------------------------------------------------------------------------
# file path definitions
# -------------------------------------------------------------------------------
# Sanitize environment variables
# https://wiki.sei.cmu.edu/confluence/display/c/ENV03-C.+Sanitize+the+environment+when+invoking+external+programs
del os.environ['HOME']  # Delete $HOME env for security reason. This will make
# Path.home() to look up in the password directory (pwd module)
os.environ['PATH'] = os.confstr("CS_PATH")  # Sanitize $PATH

# Setting home path and base path
HOME_PATH = str(Path.home())
if HOME_PATH is not None:
    HOME_PATH = HOME_PATH + "/.virtscreen"
BASE_PATH = os.path.dirname(__file__)
# Path in ~/.virtscreen
X11VNC_LOG_PATH = HOME_PATH + "/x11vnc_log.txt"
X11VNC_PASSWORD_PATH = HOME_PATH + "/x11vnc_passwd"
CONFIG_PATH = HOME_PATH + "/config.json"
# Path in the program path
DEFAULT_CONFIG_PATH = BASE_PATH + "/data/config.default.json"
ICON_PATH = BASE_PATH + "/icon/icon.png"
QML_PATH = BASE_PATH + "/qml"
MAIN_QML_PATH = QML_PATH + "/main.qml"

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

    def run(self, arg: str):
        """Spawn a process
        
        Arguments:
            arg {str} -- arguments in string
        """

        args = arg.split()
        reactor.spawnProcess(self, args[0], args=args, env=os.environ)

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
    DEFAULT_VIRT_SCREEN = "VIRTUAL1"
    VIRT_SCREEN_SUFFIX = "_virt"

    def __init__(self):
        super(XRandR, self).__init__()
        self.mode_name: str
        self.screens: List[Display] = []
        self.virt: Display() = None
        self.primary: Display() = None
        self.virt_idx: int = None
        self.primary_idx: int = None
        # Primary display
        self._update_screens()

    def _update_screens(self) -> None:
        output = self.run("xrandr")
        self.primary = None
        self.virt = None
        self.screens = []
        self.primary_idx = None
        pattern = re.compile(r"^(\S*)\s+(connected|disconnected)\s+((primary)\s+)?"
                             r"((\d+)x(\d+)\+(\d+)\+(\d+)\s+)?.*$", re.M)
        for idx, match in enumerate(pattern.finditer(output)):
            screen = Display()
            screen.name = match.group(1)
            if (self.virt_idx is None) and (screen.name == self.DEFAULT_VIRT_SCREEN):
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
        if self.virt_idx == self.primary_idx:
            raise RuntimeError("Virtual screen must be selected other than the primary screen")
        if self.virt_idx is None:
            for idx, screen in enumerate(self.screens):
                if not screen.connected and not screen.active:
                    self.virt_idx = idx
                    break
            if self.virt_idx is None:
                raise RuntimeError("There is no available devices for virtual screen")
        self.virt = self.screens[self.virt_idx]
        self.primary = self.screens[self.primary_idx]

    def _add_screen_mode(self, width, height, portrait, hidpi) -> None:
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
        for sig in [signal.SIGTERM, signal.SIGHUP, signal.SIGQUIT]:
            signal.signal(sig, self._signal_handler)

    def _signal_handler(self, signum=None, frame=None) -> None:
        self.delete_virtual_screen()
        os._exit(0)

    def get_primary_screen(self) -> Display:
        self._update_screens()
        return self.primary

    def get_virtual_screen(self) -> Display:
        self._update_screens()
        return self.virt

    def create_virtual_screen(self, width, height, portrait=False, hidpi=False) -> None:
        print("creating: ", self.virt)
        self._add_screen_mode(width, height, portrait, hidpi)
        self.check_output(f"xrandr --output {self.virt.name} --mode {self.mode_name}")
        self.check_output("sleep 5")
        self.check_output(f"xrandr --output {self.virt.name} --preferred")
        self._update_screens()

    def delete_virtual_screen(self) -> None:
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
    onVirtScreenIndexChanged = pyqtSignal(int)
    onVncUsePasswordChanged = pyqtSignal(bool)
    onVncStateChanged = pyqtSignal(VNCState)
    onIPAddressesChanged = pyqtSignal()
    onDisplaySettingClosed = pyqtSignal()
    onError = pyqtSignal(str)

    def __init__(self, parent=None):
        super(Backend, self).__init__(parent)
        # Virtual screen properties
        self.xrandr: XRandR = XRandR()
        self._virtScreenCreated: bool = False
        self._virtScreenIndex: int = self.xrandr.virt_idx
        # VNC server properties
        self._vncUsePassword: bool = False
        self._vncState: self.VNCState = self.VNCState.OFF
        # Primary screen and mouse posistion
        self._primaryProp: DisplayProperty
        self.vncServer: ProcessProtocol

    # Qt properties
    @pyqtProperty(str, constant=True)
    def settings(self):
        try:
            with open(CONFIG_PATH, "r") as f:
                return f.read()
        except FileNotFoundError:
            with open(DEFAULT_CONFIG_PATH, "r") as f:
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
        return QQmlListProperty(DisplayProperty, self, [DisplayProperty(x) for x in self.xrandr.screens])

    @pyqtProperty(int, notify=onVirtScreenIndexChanged)
    def virtScreenIndex(self):
        return self._virtScreenIndex

    @virtScreenIndex.setter
    def virtScreenIndex(self, virtScreenIndex):
        print("Changing virt to ", virtScreenIndex)
        self.xrandr.virt_idx = virtScreenIndex
        self.xrandr.virt = self.xrandr.screens[self.xrandr.virt_idx]
        self._virtScreenIndex = virtScreenIndex

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

    @pyqtProperty(DisplayProperty)
    def primary(self):
        self._primaryProp = DisplayProperty(self.xrandr.get_primary_screen())
        return self._primaryProp

    @pyqtProperty(int)
    def cursor_x(self):
        cursor = QCursor().pos()
        return cursor.x()

    @pyqtProperty(int)
    def cursor_y(self):
        cursor = QCursor().pos()
        return cursor.y()

    # Qt Slots
    @pyqtSlot(int, int, bool, bool)
    def createVirtScreen(self, width, height, portrait, hidpi):
        print("Creating a Virtual Screen...")
        try:
            self.xrandr.create_virtual_screen(width, height, portrait, hidpi)
        except subprocess.CalledProcessError as e:
            self.onError.emit(str(e.cmd) + '\n' + e.stdout.decode('utf-8'))
            return
        self.virtScreenCreated = True

    @pyqtSlot()
    def deleteVirtScreen(self):
        print("Deleting the Virtual Screen...")
        if self.vncState is not self.VNCState.OFF:
            self.onError.emit("Turn off the VNC server first")
            self.virtScreenCreated = True
            return
        self.xrandr.delete_virtual_screen()
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
                self.onError.emit('X11VNC: Error occurred.\nDouble check if the port is already used.')
                self.vncState = self.VNCState.OFF  # TODO: better handling error state
            else:
                self.vncState = self.VNCState.OFF
            print("VNC Exited.")
            atexit.unregister(self.stopVNC)

        logfile = open(X11VNC_LOG_PATH, "wb")
        self.vncServer = ProcessProtocol(_onConnected, _onReceived, _onReceived, _onEnded, logfile)
        virt = self.xrandr.get_virtual_screen()
        clip = f"{virt.width}x{virt.height}+{virt.x_offset}+{virt.y_offset}"
        arg = f"x11vnc -multiptr -repeat -rfbport {port} -clip {clip}"
        if self.vncUsePassword:
            arg += f" -rfbauth {X11VNC_PASSWORD_PATH}"
        self.vncServer.run(arg)
        # auto stop on exit
        atexit.register(self.stopVNC, force=True)

    @pyqtSlot()
    def openDisplaySetting(self):
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

        program_list = ["gnome-control-center display", "arandr"]
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
            time.sleep(2)  # Make sure X11VNC shutdown before execute next atexit().
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


# -------------------------------------------------------------------------------
# Main Code
# -------------------------------------------------------------------------------
def main():
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    app = QApplication(sys.argv)

    from PyQt5.QtWidgets import QSystemTrayIcon, QMessageBox

    if not QSystemTrayIcon.isSystemTrayAvailable():
        QMessageBox.critical(None, "VirtScreen",
                             "Cannot detect system tray on this system.")
        sys.exit(1)

    if os.environ['XDG_SESSION_TYPE'] == 'wayland':
        QMessageBox.critical(None, "VirtScreen",
                             "Currently Wayland is not supported")
        sys.exit(1)
    if not HOME_PATH:
        QMessageBox.critical(None, "VirtScreen",
                             "Cannot detect home directory.")
        sys.exit(1)
    if not os.path.exists(HOME_PATH):
        try:
            os.makedirs(HOME_PATH)
        except:
            QMessageBox.critical(None, "VirtScreen",
                                 "Cannot create ~/.virtscreen")
            sys.exit(1)

    import qt5reactor  # pylint: disable=E0401

    qt5reactor.install()
    from twisted.internet import utils, reactor  # pylint: disable=E0401

    app.setWindowIcon(QIcon(ICON_PATH))
    os.environ["QT_QUICK_CONTROLS_STYLE"] = "Material"
    # os.environ["QT_QUICK_CONTROLS_STYLE"] = "Fusion"

    # Register the Python type.  Its URI is 'People', it's v1.0 and the type
    # will be called 'Person' in QML.
    qmlRegisterType(DisplayProperty, 'VirtScreen.DisplayProperty', 1, 0, 'DisplayProperty')
    qmlRegisterType(Backend, 'VirtScreen.Backend', 1, 0, 'Backend')

    # Create a component factory and load the QML script.
    engine = QQmlApplicationEngine()
    engine.load(QUrl(MAIN_QML_PATH))
    if not engine.rootObjects():
        QMessageBox.critical(None, "VirtScreen", "Failed to load QML")
        sys.exit(1)
    sys.exit(app.exec_())
    reactor.run()

if __name__ == '__main__':
    main()
