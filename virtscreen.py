#!/usr/bin/env python

import os, re
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import pyqtSlot, Qt
from PyQt5.QtWidgets import (QAction, QApplication, QCheckBox, QComboBox,
        QDialog, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit,
        QMessageBox, QMenu, QPushButton, QSpinBox, QStyle, QSystemTrayIcon,
        QTextEdit, QVBoxLayout, QListWidget)
from twisted.internet import protocol, error
from netifaces import interfaces, ifaddresses, AF_INET
import subprocess
import atexit, signal

#-------------------------------------------------------------------------------
# PATH definitions
#-------------------------------------------------------------------------------
HOME_PATH = os.getenv('HOME', None)
if HOME_PATH is not None:
    HOME_PATH = HOME_PATH + "/.virtscreen"
X11VNC_LOG_PATH = HOME_PATH + "/x11vnc_log.txt"
X11VNC_PASSWORD_PATH = HOME_PATH + "/x11vnc_passwd"
CONFIG_PATH = HOME_PATH + "/config"

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
# Screen adjustment class
#-------------------------------------------------------------------------------
class XRandR:
    def __init__(self):
        self.mode_name: str
        self.scrren_suffix = "_virt"
        # Thoese will be created in set_virtual_screen()
        self.virt = DisplayProperty()
        self.virt.name = "VIRTUAL1"
        # Primary display
        self.primary = DisplayProperty()
        self._update_primary_screen()
    
    def _call(self, arg) -> None:
        with open(os.devnull, "w") as nulldev:
            subprocess.call(arg.split(), stdout=nulldev, stderr=nulldev)

    def _check_call(self, arg) -> None:
        with open(os.devnull, "w") as nulldev:
            subprocess.check_call(arg.split(), stdout=nulldev, stderr=nulldev)
    
    def _run(self, arg: str) -> str:
        return subprocess.run(arg.split(), stdout=subprocess.PIPE).stdout.decode('utf-8')
    
    def _add_screen_mode(self) -> None:
        args_addmode = f"xrandr --addmode {self.virt.name} {self.mode_name}"
        try:
            self._check_call(args_addmode)
        except subprocess.CalledProcessError:
            # When failed create mode and then add again
            output = self._run(f"cvt {self.virt.width} {self.virt.height}")
            mode = re.search(r"^.*Modeline\s*\".*\"\s*(.*)$", output, re.M).group(1)
            # Create new screen mode
            self._check_call(f"xrandr --newmode {self.mode_name} {mode}")
            # Add mode again
            self._check_call(args_addmode)
        # After adding mode the program should delete the mode automatically on exit
        atexit.register(self.delete_virtual_screen)
        for sig in [signal.SIGTERM, signal.SIGHUP, signal.SIGQUIT]:
            signal.signal(sig, self._signal_handler)
    
    def _update_primary_screen(self) -> None:
        output = self._run("xrandr")
        match = re.search(r"^(\w*)\s+.*primary\s*(\d+)x(\d+)\+(\d+)\+(\d+).*$", output, re.M)
        self.primary.name = match.group(1)
        self.primary.width = int(match.group(2))
        self.primary.height = int(match.group(3))
        self.primary.x_offset = int(match.group(4))
        self.primary.y_offset = int(match.group(5))

    def _update_virtual_screen(self) -> None:
        output = self._run("xrandr")
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
        self._check_call(f"xrandr --output {self.virt.name} --mode {self.mode_name}")
        self._check_call("sleep 5")
        self._check_call(f"xrandr --output {self.virt.name} --auto")
        self._update_primary_screen()
        self._update_virtual_screen()

    def delete_virtual_screen(self) -> None:
        try:
            self.virt.name
            self.mode_name
        except AttributeError:
            return
        self._call(f"xrandr --output {self.virt.name} --off")
        self._call(f"xrandr --delmode {self.virt.name} {self.mode_name}")
    
#-------------------------------------------------------------------------------
# Twisted class
#-------------------------------------------------------------------------------
class ProcessProtocol(protocol.ProcessProtocol):
    def __init__(self, onOutReceived, onErrRecevied, onProcessEnded, logfile=None):
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
        self.transport.closeStdin() # No more input

    def outReceived(self, data):
        print("outReceived! with %d bytes!" % len(data))
        self.onOutReceived(data)
        if self.logfile is not None:
            self.logfile.write(data)

    def errReceived(self, data):
        print("outReceived! with %d bytes!" % len(data))
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
# Qt Window class
#-------------------------------------------------------------------------------
class Window(QDialog):
    def __init__(self):
        super(Window, self).__init__()
        # Create objects
        self.createDisplayGroupBox()
        self.createVNCGroupBox()
        self.createBottomLayout()
        self.createActions()
        self.createTrayIcon()
        self.xrandr = XRandR()
        # Additional attributes
        self.isDisplayCreated = False
        self.isVNCRunning = False
        self.isQuitProgramPending = False
        # Update UI
        self.update_ip_address()
        # Put togather
        mainLayout = QVBoxLayout()
        mainLayout.addWidget(self.displayGroupBox)
        mainLayout.addWidget(self.VNCGroupBox)
        mainLayout.addLayout(self.bottomLayout)
        self.setLayout(mainLayout)
        # Events
        self.trayIcon.activated.connect(self.iconActivated)
        self.createDisplayButton.pressed.connect(self.createDisplayPressed)
        self.startVNCButton.pressed.connect(self.startVNCPressed)
        self.bottomQuitButton.pressed.connect(self.quitProgram)
        # Show
        icon = QIcon("icon.png")
        self.trayIcon.setIcon(icon)
        self.setWindowIcon(icon)
        self.trayIcon.show()
        self.trayIcon.setToolTip("VirtScreen")
        self.setWindowTitle("VirtScreen")
        self.resize(400, 300)
    
    def setVisible(self, visible):
        """Override of setVisible(bool)
        
        Arguments:
            visible {bool} -- true to show, false to hide
        """
        self.openAction.setEnabled(self.isMaximized() or not visible)
        super(Window, self).setVisible(visible)

    def closeEvent(self, event):
        """Override of closeEvent()
        
        Arguments:
            event {QCloseEvent} -- QCloseEvent
        """
        if self.trayIcon.isVisible():
            self.hide()
            self.showMessage()
            event.ignore()
        else:
            QApplication.instance().quit()

    @pyqtSlot()
    def createDisplayPressed(self):
        if not self.isDisplayCreated:
            # Create virtual screen
            self.createDisplayButton.setEnabled(False)
            width = self.displayWidthSpinBox.value()
            height = self.displayHeightSpinBox.value()
            portrait = self.displayPortraitCheckBox.isChecked()
            hidpi = self.displayHIDPICheckBox.isChecked()
            self.xrandr.set_virtual_screen(width, height, portrait, hidpi)
            self.xrandr.create_virtual_screen()
            self.createDisplayButton.setText("Disable the virtual display")
            self.isDisplayCreated = True
            self.createDisplayButton.setEnabled(True)
            self.startVNCButton.setEnabled(True)
        else:
            # Delete the screen
            self.createDisplayButton.setEnabled(False)
            self.xrandr.delete_virtual_screen()
            self.isDisplayCreated = False
            self.createDisplayButton.setText("Create a Virtual Display")
            self.createDisplayButton.setEnabled(True)
            self.startVNCButton.setEnabled(False)
        self.createDisplayAction.setEnabled(not self.isDisplayCreated)
        self.deleteDisplayAction.setEnabled(self.isDisplayCreated)
        self.startVNCAction.setEnabled(self.isDisplayCreated)
        self.stopVNCAction.setEnabled(False)
        
    @pyqtSlot()
    def startVNCPressed(self):
        if not self.isVNCRunning:
            self.startVNC()
        else:
            self.VNCServer.kill()

    @pyqtSlot('QSystemTrayIcon::ActivationReason')
    def iconActivated(self, reason):
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
            if self.isVisible():
                self.hide()
            else:
                self.showNormal()
        elif reason == QSystemTrayIcon.MiddleClick:
            self.showMessage()

    @pyqtSlot()
    def showMessage(self):
        icon = QSystemTrayIcon.MessageIcon(QSystemTrayIcon.Information)
        self.trayIcon.showMessage("VirtScreen is running",
                "The program will keep running in the system tray. To \n"
                "terminate the program, choose \"Quit\" in the \n"
                "context menu of the system tray entry.",
                icon,
                7 * 1000)

    @pyqtSlot()
    def quitProgram(self):
        self.isQuitProgramPending = True
        try:
            # Rest of quit sequence will be handled in the callback.
            self.VNCServer.kill()
        except (AttributeError, error.ProcessExitedAlready):
            self.xrandr.delete_virtual_screen()
            QApplication.instance().quit()

    def createDisplayGroupBox(self):
        self.displayGroupBox = QGroupBox("Virtual Display Settings")

        # Resolution Row
        resolutionLabel = QLabel("Resolution:")

        self.displayWidthSpinBox = QSpinBox()
        self.displayWidthSpinBox.setRange(640, 1920)
        self.displayWidthSpinBox.setSuffix("px")
        self.displayWidthSpinBox.setValue(1368)

        xLabel = QLabel("x")

        self.displayHeightSpinBox = QSpinBox()
        self.displayHeightSpinBox.setRange(360, 1080)
        self.displayHeightSpinBox.setSuffix("px")
        self.displayHeightSpinBox.setValue(1024)

        # Portrait and HiDPI
        self.displayPortraitCheckBox = QCheckBox("Portrait Mode")
        self.displayPortraitCheckBox.setChecked(False)

        self.displayHIDPICheckBox = QCheckBox("HiDPI (2x resolution)")
        self.displayHIDPICheckBox.setChecked(False)

        # Start button
        self.createDisplayButton = QPushButton("Create a Virtual Display")
        self.createDisplayButton.setDefault(True)

        # Notice Label
        self.displayNoticeLabel = QLabel("After creating, you can adjust the display's " +
                                "position in the Desktop Environment's settings " +
                                "or ARandR.")
        self.displayNoticeLabel.setWordWrap(True)
        font = self.displayNoticeLabel.font()
        font.setPointSize(9)
        self.displayNoticeLabel.setFont(font)

        # Putting them together
        layout = QVBoxLayout()

        # Grid layout for screen settings
        gridLayout = QGridLayout()
        # Resolution row
        rowLayout = QHBoxLayout()
        rowLayout.addWidget(resolutionLabel)
        rowLayout.addWidget(self.displayWidthSpinBox)
        rowLayout.addWidget(xLabel)
        rowLayout.addWidget(self.displayHeightSpinBox)
        rowLayout.addStretch()
        layout.addLayout(rowLayout)
        # Portrait & HiDPI
        rowLayout = QHBoxLayout()
        rowLayout.addWidget(self.displayPortraitCheckBox)
        rowLayout.addWidget(self.displayHIDPICheckBox)
        rowLayout.addStretch()
        layout.addLayout(rowLayout)
        # Display create button and Notice label
        layout.addWidget(self.createDisplayButton)
        layout.addWidget(self.displayNoticeLabel)

        self.displayGroupBox.setLayout(layout)

    def createVNCGroupBox(self):
        self.VNCGroupBox = QGroupBox("VNC Server")

        portLabel = QLabel("Port:")
        self.VNCPortSpinBox = QSpinBox()
        self.VNCPortSpinBox.setRange(1, 65535)
        self.VNCPortSpinBox.setValue(5900)

        passwordLabel = QLabel("Password:")
        self.VNCPasswordLineEdit = QLineEdit()
        self.VNCPasswordLineEdit.setText("")

        IPLabel = QLabel("Connect a VNC client to one of:")
        self.VNCIPListWidget = QListWidget()

        self.startVNCButton = QPushButton("Start VNC Server")
        self.startVNCButton.setDefault(False)
        self.startVNCButton.setEnabled(False)

        # Set Overall layout
        layout = QVBoxLayout()
        rowLayout = QHBoxLayout()
        rowLayout.addWidget(portLabel)
        rowLayout.addWidget(self.VNCPortSpinBox)
        rowLayout.addWidget(passwordLabel)
        rowLayout.addWidget(self.VNCPasswordLineEdit)
        layout.addLayout(rowLayout)
        layout.addWidget(self.startVNCButton)
        layout.addWidget(IPLabel)
        layout.addWidget(self.VNCIPListWidget)
        self.VNCGroupBox.setLayout(layout)
    
    def createBottomLayout(self):
        self.bottomLayout = QVBoxLayout()

        # Create button
        self.bottomQuitButton = QPushButton("Quit")
        self.bottomQuitButton.setDefault(False)
        self.bottomQuitButton.setEnabled(True)

        # Set Overall layout
        hLayout = QHBoxLayout()
        hLayout.addStretch()
        hLayout.addWidget(self.bottomQuitButton)
        self.bottomLayout.addLayout(hLayout)

    def createActions(self):
        self.createDisplayAction = QAction("Create display", self)
        self.createDisplayAction.triggered.connect(self.createDisplayPressed)
        self.createDisplayAction.setEnabled(True)

        self.deleteDisplayAction = QAction("Disable display", self)
        self.deleteDisplayAction.triggered.connect(self.createDisplayPressed)
        self.deleteDisplayAction.setEnabled(False)

        self.startVNCAction = QAction("&Start sharing", self)
        self.startVNCAction.triggered.connect(self.startVNCPressed)
        self.startVNCAction.setEnabled(False)

        self.stopVNCAction = QAction("S&top sharing", self)
        self.stopVNCAction.triggered.connect(self.startVNCPressed)
        self.stopVNCAction.setEnabled(False)
        
        self.openAction = QAction("&Open VirtScreen", self)
        self.openAction.triggered.connect(self.showNormal)

        self.quitAction = QAction("&Quit", self)
        self.quitAction.triggered.connect(self.quitProgram)

    def createTrayIcon(self):
        self.trayIconMenu = QMenu(self)
        self.trayIconMenu.addAction(self.createDisplayAction)
        self.trayIconMenu.addAction(self.deleteDisplayAction)
        self.trayIconMenu.addSeparator()
        self.trayIconMenu.addAction(self.startVNCAction)
        self.trayIconMenu.addAction(self.stopVNCAction)
        self.trayIconMenu.addSeparator()
        self.trayIconMenu.addAction(self.openAction)
        self.trayIconMenu.addSeparator()
        self.trayIconMenu.addAction(self.quitAction)

        self.trayIcon = QSystemTrayIcon(self)
        self.trayIcon.setContextMenu(self.trayIconMenu)
    
    def update_ip_address(self):
        self.VNCIPListWidget.clear()
        for interface in interfaces():
            if interface == 'lo':
                continue
            addresses = ifaddresses(interface).get(AF_INET, None)
            if addresses is None:
                continue
            for link in addresses:
                if link is not None:
                    self.VNCIPListWidget.addItem(link['addr'])
    
    def startVNC(self):
        def _onReceived(data):
            data = data.decode("utf-8")
            for line in data.splitlines():
                # TODO: Update state of the server
                pass
        def _onEnded(exitCode):
            self.startVNCButton.setEnabled(False)
            self.isVNCRunning = False
            if self.isQuitProgramPending:
                self.xrandr.delete_virtual_screen()
                QApplication.instance().quit()
            self.startVNCButton.setText("Start VNC Server")
            self.startVNCButton.setEnabled(True)
            self.createDisplayButton.setEnabled(True)
            self.deleteDisplayAction.setEnabled(True)
            self.startVNCAction.setEnabled(True)
            self.stopVNCAction.setEnabled(False)
        # Setting UI before starting
        self.createDisplayButton.setEnabled(False)
        self.createDisplayAction.setEnabled(False)
        self.deleteDisplayAction.setEnabled(False)
        self.startVNCButton.setEnabled(False)
        self.startVNCButton.setText("Running...")
        self.startVNCAction.setEnabled(False)
        # Set password
        isPassword = False
        if self.VNCPasswordLineEdit.text():
            isPassword = True
            p = SubprocessWrapper()
            try:
                p.run(f"x11vnc -storepasswd {self.VNCPasswordLineEdit.text()} {X11VNC_PASSWORD_PATH}")
            except:
                isPassword = False
        # Run VNC server
        self.isVNCRunning = True
        logfile = open(X11VNC_LOG_PATH, "wb")
        self.VNCServer = ProcessProtocol(_onReceived, _onReceived, _onEnded, logfile)
        port = self.VNCPortSpinBox.value()
        virt = self.xrandr.get_virtual_screen()
        clip = f"{virt.width}x{virt.height}+{virt.x_offset}+{virt.y_offset}"
        arg = f"x11vnc -multiptr -repeat -rfbport {port} -clip {clip}"
        if isPassword:
            arg += f" -rfbauth {X11VNC_PASSWORD_PATH}"
        self.VNCServer.run(arg)
        self.update_ip_address()
        # Change UI
        self.startVNCButton.setEnabled(True)
        self.startVNCButton.setText("Stop Sharing")
        self.stopVNCAction.setEnabled(True)

#-------------------------------------------------------------------------------
# Main Code
#-------------------------------------------------------------------------------
if __name__ == '__main__':

    import sys

    app = QApplication(sys.argv)

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

    QApplication.setQuitOnLastWindowClosed(False)
    window = Window()
    window.show()
    sys.exit(app.exec_())
    reactor.run()
