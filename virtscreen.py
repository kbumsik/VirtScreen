#!/usr/bin/env python

import sys, os, subprocess, signal, re, atexit, time
from enum import Enum
from typing import List

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import  QObject, QUrl, Qt, pyqtProperty, pyqtSlot, pyqtSignal, Q_ENUMS
from PyQt5.QtGui import QIcon, QCursor
from PyQt5.QtQml import qmlRegisterType, QQmlApplicationEngine, QQmlListProperty

from twisted.internet import protocol, error
from netifaces import interfaces, ifaddresses, AF_INET

#-------------------------------------------------------------------------------
# file path definitions
#-------------------------------------------------------------------------------
HOME_PATH = os.getenv('HOME', None)
if HOME_PATH is not None:
    HOME_PATH = HOME_PATH + "/.virtscreen"
X11VNC_LOG_PATH = HOME_PATH + "/x11vnc_log.txt"
X11VNC_PASSWORD_PATH = HOME_PATH + "/x11vnc_passwd"
CONFIG_PATH = HOME_PATH + "/config"

PROGRAM_PATH = "."
ICON_PATH = PROGRAM_PATH + "/icon/icon.png"
ICON_TABLET_OFF_PATH = PROGRAM_PATH + "/icon/icon_tablet_off.png"
ICON_TABLET_ON_PATH = PROGRAM_PATH + "/icon/icon_tablet_on.png"

#-------------------------------------------------------------------------------
# Subprocess wrapper
#-------------------------------------------------------------------------------
class SubprocessWrapper:
    def __init__(self, stdout:str=os.devnull, stderr:str=os.devnull):
        self.stdout: str = stdout
        self.stderr: str = stderr
    
    def call(self, arg) -> None:
        with open(os.devnull, "w") as f:
            subprocess.call(arg.split(), stdout=f, stderr=f)

    def check_call(self, arg) -> None:
        with open(os.devnull, "w") as f:
            subprocess.check_call(arg.split(), stdout=f, stderr=f)
    
    def run(self, arg: str) -> str:
        return subprocess.run(arg.split(), stdout=subprocess.PIPE).stdout.decode('utf-8')

#-------------------------------------------------------------------------------
# Display properties
#-------------------------------------------------------------------------------
class DisplayProperty(QObject):
    def __init__(self, parent=None):
        super(DisplayProperty, self).__init__(parent)
        self._name: str
        self._primary: bool
        self._connected: bool
        self._active: bool
        self._width: int
        self._height: int
        self._x_offset: int
        self._y_offset: int
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
            ret += " not active"
        return ret
    
    @pyqtProperty(str, constant=True)
    def name(self):
        return self._name
    @name.setter
    def name(self, name):
        self._name = name

    @pyqtProperty(bool, constant=True)
    def primary(self):
        return self._primary
    @primary.setter
    def primary(self, primary):
        self._primary = primary

    @pyqtProperty(bool, constant=True)
    def connected(self):
        return self._connected
    @connected.setter
    def connected(self, connected):
        self._connected = connected

    @pyqtProperty(bool, constant=True)
    def active(self):
        return self._active
    @active.setter
    def active(self, active):
        self._active = active

    @pyqtProperty(int, constant=True)
    def width(self):
        return self._width
    @width.setter
    def width(self, width):
        self._width = width

    @pyqtProperty(int, constant=True)
    def height(self):
        return self._height
    @height.setter
    def height(self, height):
        self._height = height

    @pyqtProperty(int, constant=True)
    def x_offset(self):
        return self._x_offset
    @x_offset.setter
    def x_offset(self, x_offset):
        self._x_offset = x_offset

    @pyqtProperty(int, constant=True)
    def y_offset(self):
        return self._y_offset
    @y_offset.setter
    def y_offset(self, y_offset):
        self._y_offset = y_offset

#-------------------------------------------------------------------------------
# Screen adjustment class
#-------------------------------------------------------------------------------
class XRandR(SubprocessWrapper):
    DEFAULT_VIRT_SCREEN = "VIRTUAL1"
    VIRT_SCREEN_SUFFIX = "_virt"

    def __init__(self):
        super(XRandR, self).__init__()
        self.mode_name: str
        self.screens: List[DisplayProperty] = []
        self.virt: DisplayProperty() = None
        self.primary: DisplayProperty() = None
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
            screen = DisplayProperty()
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
            raise RuntimeError("VIrtual screen must be selected other than the primary screen")
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
            self.virt.width = 2 * self.virt.width
            self.virt.height = 2 * self.virt.height
        self.mode_name = str(self.virt.width) + "x" + str(self.virt.height) + self.VIRT_SCREEN_SUFFIX
        # Then create using xrandr command
        args_addmode = f"xrandr --addmode {self.virt.name} {self.mode_name}"
        try:
            self.check_call(args_addmode)
        except subprocess.CalledProcessError:
            # When failed create mode and then add again
            output = self.run(f"cvt {self.virt.width} {self.virt.height}")
            mode = re.search(r"^.*Modeline\s*\".*\"\s*(.*)$", output, re.M).group(1)
            # Create new screen mode
            self.check_call(f"xrandr --newmode {self.mode_name} {mode}")
            # Add mode again
            self.check_call(args_addmode)
        # After adding mode the program should delete the mode automatically on exit
        atexit.register(self.delete_virtual_screen)
        for sig in [signal.SIGTERM, signal.SIGHUP, signal.SIGQUIT]:
            signal.signal(sig, self._signal_handler)

    def _signal_handler(self, signum=None, frame=None) -> None:
        self.delete_virtual_screen()
        os._exit(0)

    def get_primary_screen(self) -> DisplayProperty:
        self._update_screens()
        return self.primary

    def get_virtual_screen(self) -> DisplayProperty:
        self._update_screens()
        return self.virt
    
    def create_virtual_screen(self, width, height, portrait=False, hidpi=False) -> None:
        print("creating: ", self.virt)
        self._add_screen_mode(width, height, portrait, hidpi)
        self.check_call(f"xrandr --output {self.virt.name} --mode {self.mode_name}")
        self.check_call("sleep 5")
        self.check_call(f"xrandr --output {self.virt.name} --preferred")
        self._update_screens()

    def delete_virtual_screen(self) -> None:
        try:
            self.virt.name
            self.mode_name
        except AttributeError:
            return
        self.call(f"xrandr --output {self.virt.name} --off")
        self.call(f"xrandr --delmode {self.virt.name} {self.mode_name}")
        atexit.unregister(self.delete_virtual_screen)
        self._update_screens()
        
#-------------------------------------------------------------------------------
# Twisted class
#-------------------------------------------------------------------------------
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
        self.transport.closeStdin() # No more input

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

#-------------------------------------------------------------------------------
# QML Backend class
#-------------------------------------------------------------------------------
class Backend(QObject):
    """ Backend class for QML frontend """
    class VNCState:
        """ Enum to indicate a state of the VNC server """
        OFF = 0
        WAITING = 1
        CONNECTED = 2

    Q_ENUMS(VNCState)

    # Signals
    onVirtScreenCreatedChanged = pyqtSignal(bool)
    onVirtScreenIndexChanged = pyqtSignal(int)
    onVncStateChanged = pyqtSignal(VNCState)
    onIPAddressesChanged = pyqtSignal()

    def __init__(self, parent=None):
        super(Backend, self).__init__(parent)
        # objects
        self.xrandr = XRandR()
        # Virtual screen properties
        self._virt = DisplayProperty()
        self.virt.width = 1368
        self.virt.height = 1024
        self._portrait = False
        self._hidpi = False
        self._virtScreenCreated = False
        self._screens: List[DisplayProperty] = self.xrandr.screens
        self._virtScreenIndex = self.xrandr.virt_idx
        # VNC server properties
        self._vncPort = 5900
        self._vncPassword = ""
        self._vncState = Backend.VNCState.OFF
        self._ipAddresses: List[str] = []
        self.updateIPAddresses()
        # Primary screen and mouse posistion
        self._primary: DisplayProperty() = self.xrandr.get_primary_screen()
        self._cursor_x: int
        self._cursor_y: int
        
    # Qt properties
    @pyqtProperty(DisplayProperty)
    def virt(self):
        return self._virt
    @virt.setter
    def virt(self, virt):
        self._virt = virt

    @pyqtProperty(bool)
    def portrait(self):
        return self._portrait
    @portrait.setter
    def portrait(self, portrait):
        self._portrait = portrait

    @pyqtProperty(bool)
    def hidpi(self):
        return self._hidpi
    @hidpi.setter
    def hidpi(self, hidpi):
        self._hidpi = hidpi
    
    @pyqtProperty(bool, notify=onVirtScreenCreatedChanged)
    def virtScreenCreated(self):
        return self._virtScreenCreated
    @virtScreenCreated.setter
    def virtScreenCreated(self, value):
        self._virtScreenCreated = value
        self.onVirtScreenCreatedChanged.emit(value)
        
    @pyqtProperty(QQmlListProperty)
    def screens(self):
        return QQmlListProperty(DisplayProperty, self, self._screens)

    @pyqtProperty(int, notify=onVirtScreenIndexChanged)
    def virtScreenIndex(self):
        return self._virtScreenIndex
    @virtScreenIndex.setter
    def virtScreenIndex(self, virtScreenIndex):
        print("Changing virt to ", virtScreenIndex)
        self.xrandr.virt_idx = virtScreenIndex
        self.xrandr.virt = self.xrandr.screens[self.xrandr.virt_idx]
        self._virtScreenIndex = virtScreenIndex

    @pyqtProperty(int)
    def vncPort(self):
        return self._vncPort
    @vncPort.setter
    def vncPort(self, port):
        self._vncPort = port

    @pyqtProperty(str)
    def vncPassword(self):
        return self._vncPassword
    @vncPassword.setter
    def vncPassword(self, vncPassword):
        self._vncPassword = vncPassword

    @pyqtProperty(VNCState, notify=onVncStateChanged)
    def vncState(self):
        return self._vncState
    @vncState.setter
    def vncState(self, state):
        self._vncState = state
        self.onVncStateChanged.emit(self._vncState)

    @pyqtProperty('QStringList', notify=onIPAddressesChanged)
    def ipAddresses(self):
        return self._ipAddresses
    
    @pyqtProperty(DisplayProperty)
    def primary(self):
        self._primary = self.xrandr.get_primary_screen()
        return self._primary

    @pyqtProperty(int)
    def cursor_x(self):
        cursor = QCursor().pos()
        self._cursor_x = cursor.x()
        return self._cursor_x

    @pyqtProperty(int)
    def cursor_y(self):
        cursor = QCursor().pos()
        self._cursor_y = cursor.y()
        return self._cursor_y
    
    # Qt Slots
    @pyqtSlot()
    def createVirtScreen(self):
        print("Creating a Virtual Screen...")
        self.xrandr.create_virtual_screen(self.virt.width, self.virt.height, self.portrait, self.hidpi)
        self.virtScreenCreated = True
        
    @pyqtSlot()
    def deleteVirtScreen(self):
        print("Deleting the Virtual Screen...")
        if self.vncState is not Backend.VNCState.OFF:
            print("Turn off the VNC server first")
            self.virtScreenCreated = True
            return
        self.xrandr.delete_virtual_screen()
        self.virtScreenCreated = False
    
    @pyqtSlot()
    def startVNC(self):
        # Check if a virtual screen created
        if not self.virtScreenCreated:
            print("Virtual Screen not crated.")
            return
        # regex used in callbacks
        re_connection = re.compile(r"^.*Got connection from client.*$", re.M)
        # define callbacks
        def _onConnected():
            print("VNC started.")
            self.vncState = Backend.VNCState.WAITING
        def _onReceived(data):
            data = data.decode("utf-8")
            if (self._vncState is not Backend.VNCState.CONNECTED) and re_connection.search(data):
                print("VNC connected.")
                self.vncState = Backend.VNCState.CONNECTED
        def _onEnded(exitCode):
            print("VNC Exited.")
            self.vncState = Backend.VNCState.OFF
            atexit.unregister(self.stopVNC)
        # Set password
        password = False
        if self.vncPassword:
            print("There is password. Creating.")
            password = True
            p = SubprocessWrapper()
            try:
                p.run(f"x11vnc -storepasswd {self.vncPassword} {X11VNC_PASSWORD_PATH}")
            except:
                password = False
        logfile = open(X11VNC_LOG_PATH, "wb")
        self.vncServer = ProcessProtocol(_onConnected, _onReceived, _onReceived, _onEnded, logfile)
        port = self.vncPort
        virt = self.xrandr.get_virtual_screen()
        clip = f"{virt.width}x{virt.height}+{virt.x_offset}+{virt.y_offset}"
        arg = f"x11vnc -multiptr -repeat -rfbport {port} -clip {clip}"
        if password:
            arg += f" -rfbauth {X11VNC_PASSWORD_PATH}"
        self.vncServer.run(arg)
        # auto stop on exit
        atexit.register(self.stopVNC, force=True)

    @pyqtSlot()
    def stopVNC(self, force=False):
        if force:
            # Usually called from atexit().
            self.vncServer.kill()
            time.sleep(2)   # Make sure X11VNC shutdown before execute next atexit.
        if self._vncState in (Backend.VNCState.WAITING, Backend.VNCState.CONNECTED):
            self.vncServer.kill()
        else:
            print("stopVNC called while it is not running")

    @pyqtSlot()
    def updateIPAddresses(self):
        self._ipAddresses.clear()
        for interface in interfaces():
            if interface == 'lo':
                continue
            addresses = ifaddresses(interface).get(AF_INET, None)
            if addresses is None:
                continue
            for link in addresses:
                if link is not None:
                    self._ipAddresses.append(link['addr'])
        self.onIPAddressesChanged.emit()

    @pyqtSlot()
    def quitProgram(self):
        QApplication.instance().quit()

#-------------------------------------------------------------------------------
# Main Code
#-------------------------------------------------------------------------------
if __name__ == '__main__':
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    app = QApplication(sys.argv)

    from PyQt5.QtWidgets import QSystemTrayIcon, QMessageBox

    if not QSystemTrayIcon.isSystemTrayAvailable():
        QMessageBox.critical(None, "VirtScreen",
                "I couldn't detect any system tray on this system.")
        sys.exit(1)

    if os.environ['XDG_SESSION_TYPE'] == 'wayland':
        QMessageBox.critical(None, "VirtScreen",
                            "Currently Wayland is not supported")
        sys.exit(1)
    if HOME_PATH is None:
        QMessageBox.critical(None, "VirtScreen",
                            "VirtScreen cannot detect $HOME")
        sys.exit(1)
    if not os.path.exists(HOME_PATH):
        try:
            os.makedirs(HOME_PATH)
        except:
            QMessageBox.critical(None, "VirtScreen",
                                "VirtScreen cannot create ~/.virtscreen")
            sys.exit(1)
    
    import qt5reactor # pylint: disable=E0401
    qt5reactor.install()
    from twisted.internet import utils, reactor # pylint: disable=E0401

    app.setWindowIcon(QIcon(ICON_PATH))
    os.environ["QT_QUICK_CONTROLS_STYLE"] = "Material"
    # os.environ["QT_QUICK_CONTROLS_STYLE"] = "Fusion"
    
    # Register the Python type.  Its URI is 'People', it's v1.0 and the type
    # will be called 'Person' in QML.
    qmlRegisterType(DisplayProperty, 'VirtScreen.DisplayProperty', 1, 0, 'DisplayProperty')
    qmlRegisterType(Backend, 'VirtScreen.Backend', 1, 0, 'Backend')

    # Create a component factory and load the QML script.
    engine = QQmlApplicationEngine()
    engine.load(QUrl('main.qml'))
    if not engine.rootObjects():
        QMessageBox.critical(None, "VirtScreen", "Failed to load qml")
        sys.exit(1)
    sys.exit(app.exec_())
    reactor.run()
