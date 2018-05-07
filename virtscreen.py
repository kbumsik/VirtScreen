#!/usr/bin/env python

import sys, os, subprocess, signal, re, atexit, time
from enum import Enum

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import  QObject, QUrl, Qt
from PyQt5.QtCore import pyqtProperty, pyqtSlot, pyqtSignal
from PyQt5.QtGui import QIcon, QCursor
from PyQt5.QtQml import qmlRegisterType, QQmlApplicationEngine

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
class DisplayProperty:
    def __init__(self):
        self.name: str 
        self.width: int
        self.height: int
        self.x_offset: int
        self.y_offset: int

#-------------------------------------------------------------------------------
# Screen adjustment class
#-------------------------------------------------------------------------------
class XRandR(SubprocessWrapper):
    def __init__(self):
        super(XRandR, self).__init__()
        self.mode_name: str
        self.scrren_suffix = "_virt"
        # Thoese will be created in set_virtual_screen()
        self.virt = DisplayProperty()
        self.virt.name = "VIRTUAL1"
        # Primary display
        self.primary = DisplayProperty()
        self._update_primary_screen()
    
    def _add_screen_mode(self) -> None:
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
    
    def _update_primary_screen(self) -> None:
        output = self.run("xrandr")
        match = re.search(r"^(\w*)\s+.*primary\s*(\d+)x(\d+)\+(\d+)\+(\d+).*$", output, re.M)
        self.primary.name = match.group(1)
        self.primary.width = int(match.group(2))
        self.primary.height = int(match.group(3))
        self.primary.x_offset = int(match.group(4))
        self.primary.y_offset = int(match.group(5))

    def _update_virtual_screen(self) -> None:
        output = self.run("xrandr")
        match = re.search(r"^" + self.virt.name + r"\s+.*\s+(\d+)x(\d+)\+(\d+)\+(\d+).*$", output, re.M)
        self.virt.width = int(match.group(1))
        self.virt.height = int(match.group(2))
        self.virt.x_offset = int(match.group(3))
        self.virt.y_offset = int(match.group(4))

    def _signal_handler(self, signum=None, frame=None) -> None:
        self.delete_virtual_screen()
        os._exit(0)

    def get_virtual_screen(self) -> DisplayProperty:
        self._update_virtual_screen()
        return self.virt

    def set_virtual_screen(self, width, height, portrait=False, hidpi=False):
        self.virt.width = width
        self.virt.height = height
        if portrait:
            self.virt.width = height
            self.virt.height = width
        if hidpi:
            self.virt.width = 2 * self.virt.width
            self.virt.height = 2 * self.virt.height
        self.mode_name = str(self.virt.width) + "x" + str(self.virt.height) + self.scrren_suffix
    
    def create_virtual_screen(self) -> None:
        self._add_screen_mode()
        self.check_call(f"xrandr --output {self.virt.name} --mode {self.mode_name}")
        self.check_call("sleep 5")
        self.check_call(f"xrandr --output {self.virt.name} --auto")
        self._update_primary_screen()
        self._update_virtual_screen()

    def delete_virtual_screen(self) -> None:
        try:
            self.virt.name
            self.mode_name
        except AttributeError:
            return
        self.call(f"xrandr --output {self.virt.name} --off")
        self.call(f"xrandr --delmode {self.virt.name} {self.mode_name}")
        atexit.unregister(self.delete_virtual_screen)
        
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
class VNCState(Enum):
    """ Enum to indicate a state of the VNC server """
    OFF = "Off"
    WAITING = "Waiting"
    CONNECTED = "Connected"

class Backend(QObject):
    """ Backend class for QML frontend """
    # Signals
    virtScreenChanged = pyqtSignal(bool)
    vncStateChanged = pyqtSignal(str)

    def __init__(self, parent=None):
        super(Backend, self).__init__(parent)
        # Virtual screen properties
        self._width = 1368
        self._height = 1024
        self._portrait = False
        self._hidpi = False
        self._virtScreenCreated = False
        # VNC server properties
        self._vncPort = 5900
        self._vncPassword = ""
        self._vncState = VNCState.OFF
        # Primary screen and mouse posistion
        self._cursor_x: int
        self._cursor_y: int
        self._primaryDisplayWidth: int
        self._primaryDisplayHeight: int
        # objects
        self.xrandr = XRandR()
        
    # Qt properties
    @pyqtProperty(int)
    def width(self):
        return self._width
    @width.setter
    def width(self, width):
        self._width = width
    
    @pyqtProperty(int)
    def height(self):
        return self._height
    @height.setter
    def height(self, height):
        self._height = height

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
    
    @pyqtProperty(bool)
    def virtScreenCreated(self, notify=virtScreenChanged):
        return self._virtScreenCreated
    @virtScreenCreated.setter
    def virtScreenCreated(self, value):
        self._virtScreenCreated = value
        self.virtScreenChanged.emit(value)
        
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
        print(self._vncPassword)

    @pyqtProperty(str)
    def vncState(self, notify=vncStateChanged):
        return self._vncState.value
    @vncState.setter
    def vncState(self, state):
        self._vncState = state
        self.vncStateChanged.emit(self._vncState.value)
    
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

    @pyqtProperty(int)
    def primaryDisplayWidth(self):
        screen = QApplication.desktop().screenGeometry()
        self._primaryDisplayWidth = screen.width()
        return self._primaryDisplayWidth

    @pyqtProperty(int)
    def primaryDisplayHeight(self):
        screen = QApplication.desktop().screenGeometry()
        self._primaryDisplayHeight = screen.height()
        return self._primaryDisplayHeight
    
    # Qt Slots
    @pyqtSlot()
    def createVirtScreen(self):
        print("Creating a Virtual Screen...")
        self.xrandr.set_virtual_screen(self.width, self.height, self.portrait, self.hidpi)
        self.xrandr.create_virtual_screen()
        self.virtScreenCreated = True
        
    # Qt Slots
    @pyqtSlot()
    def deleteVirtScreen(self):
        print("Deleting the Virtual Screen...")
        if self.vncState != VNCState.OFF.value:
            print("Turn off the VNC server first")
            return
        self.xrandr.delete_virtual_screen()
        self.virtScreenCreated = False
    
    @pyqtSlot()
    def startVNC(self):
        # Check if a virtual screen created
        if not self.virtScreenCreated:
            print("Virtual Screen not crated.")
            return
        # define callbacks
        def _onConnected():
            print("VNC started.")
            self.vncState = VNCState.WAITING
        def _onReceived(data):
            data = data.decode("utf-8")
            for line in data.splitlines():
                # TODO: Update state of the server
                pass
        def _onEnded(exitCode):
            print("VNC Exited.")
            self.vncState = VNCState.OFF
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
        if self.vncState in (VNCState.WAITING.value, VNCState.CONNECTED.value):
            self.vncServer.kill()
        else:
            print("stopVNC called while it is not running")

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
    qmlRegisterType(Backend, 'VirtScreen.Backend', 1, 0, 'Backend')

    # Create a component factory and load the QML script.
    engine = QQmlApplicationEngine()
    engine.load(QUrl('main.qml'))
    if not engine.rootObjects():
        QMessageBox.critical(None, "VirtScreen", "Failed to load qml")
        sys.exit(1)
    sys.exit(app.exec_())
    reactor.run()
