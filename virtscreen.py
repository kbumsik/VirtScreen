#!/usr/bin/env python

import os, re
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import pyqtSlot, Qt
from PyQt5.QtWidgets import (QAction, QApplication, QCheckBox, QComboBox,
        QDialog, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit,
        QMessageBox, QMenu, QPushButton, QSpinBox, QStyle, QSystemTrayIcon,
        QTextEdit, QVBoxLayout, QListWidget)
from twisted.internet import protocol
from netifaces import interfaces, ifaddresses, AF_INET
import subprocess
import atexit, signal

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
    
    def create_virtual_screen(self, position) -> None:
        self._add_screen_mode()
        self._check_call(f"xrandr --output {self.virt.name} --mode {self.mode_name}")
        self._check_call("sleep 5")
        self._check_call(f"xrandr --output {self.virt.name} {position} {self.primary.name}")
        self._update_primary_screen()
        self._update_virtual_screen()

    def delete_virtual_screen(self) -> None:
        self._call(f"xrandr --output {self.virt.name} --off")
        self._call(f"xrandr --delmode {self.virt.name} {self.mode_name}")
    
#-------------------------------------------------------------------------------
# Twisted class
#-------------------------------------------------------------------------------
class ProcessProtocol(protocol.ProcessProtocol):
    def __init__(self, onOutReceived, onErrRecevied, onProcessEnded):
        self.onOutReceived = onOutReceived
        self.onErrRecevied = onErrRecevied
        self.onProcessEnded = onProcessEnded
    
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

    def errReceived(self, data):
        print("outReceived! with %d bytes!" % len(data))
        self.onErrRecevied(data)

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
        self.createActions()
        self.createTrayIcon()
        self.xrandr = XRandR()
        # Additional attributes
        self.isVNCRunning = False
        # Update UI
        self.update_ip_address()
        # Put togather
        mainLayout = QVBoxLayout()
        mainLayout.addWidget(self.displayGroupBox)
        mainLayout.addWidget(self.VNCGroupBox)
        self.setLayout(mainLayout)
        # Events
        self.trayIcon.activated.connect(self.iconActivated)
        self.startVNCButton.pressed.connect(self.startPressed)
        self.VNCMessageListWidget.model().rowsInserted.connect(
                                    self.VNCMessageListWidget.scrollToBottom)
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
    def startPressed(self):
        if self.isVNCRunning:
            self.VNCServer.kill()
        else:
            self.startVNC()

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

    def createDisplayGroupBox(self):
        self.displayGroupBox = QGroupBox("Virtual Display Settings")

        # First row
        positionLabel = QLabel("Position:")

        self.displayPositionComboBox = QComboBox()
        self.displayPositionComboBox.addItem("Right", "--right-of")
        self.displayPositionComboBox.addItem("Left", "--left-of")
        self.displayPositionComboBox.addItem("Above", "--above")
        self.displayPositionComboBox.addItem("Below", "--below")
        self.displayPositionComboBox.setCurrentIndex(0)

        self.displayPortraitCheckBox = QCheckBox("Portrait Mode")
        self.displayPortraitCheckBox.setChecked(False)

        # Second row
        resolutionLabel = QLabel("Resolution:")

        self.displayWidthSpinBox = QSpinBox()
        self.displayWidthSpinBox.setRange(640, 1920)
        self.displayWidthSpinBox.setSuffix(" px")
        self.displayWidthSpinBox.setValue(1368)

        xLabel = QLabel("x")

        self.displayHeightSpinBox = QSpinBox()
        self.displayHeightSpinBox.setRange(360, 1080)
        self.displayHeightSpinBox.setSuffix(" px")
        self.displayHeightSpinBox.setValue(1024)

        self.displayHIDPICheckBox = QCheckBox("HiDPI (2x resolution)")
        self.displayHIDPICheckBox.setChecked(False)

        # Putting them togather
        layout = QGridLayout()
        # Display Position row
        layout.addWidget(positionLabel, 0, 0)
        layout.addWidget(self.displayPositionComboBox, 0, 1, 1, 2)
        layout.addWidget(self.displayPortraitCheckBox, 0, 6, 1, 2, Qt.AlignLeft)
        # Resolution row
        layout.addWidget(resolutionLabel, 1, 0)
        layout.addWidget(self.displayWidthSpinBox, 1, 1, 1, 2)
        layout.addWidget(xLabel, 1, 3, Qt.AlignHCenter)
        layout.addWidget(self.displayHeightSpinBox, 1, 4, 1, 2)
        layout.addWidget(self.displayHIDPICheckBox, 1, 6, 1, 2, Qt.AlignLeft)
        # Set strectch
        layout.setColumnStretch(1, 0)
        layout.setColumnStretch(3, 0)
        # layout.setRowStretch(4, 1)
        
        self.displayGroupBox.setLayout(layout)

    def createVNCGroupBox(self):
        self.VNCGroupBox = QGroupBox("VNC Server")

        portLabel = QLabel("Port:")
        self.VNCPortSpinBox = QSpinBox()
        self.VNCPortSpinBox.setRange(5900, 6000)
        self.VNCPortSpinBox.setValue(5900)

        IPLabel = QLabel("Connect a VNC client to one of:")
        self.VNCIPListWidget = QListWidget()

        self.startVNCButton = QPushButton("Start VNC Server")
        self.startVNCButton.setDefault(False)

        messageLabel = QLabel("Server Messages")
        self.VNCMessageListWidget = QListWidget()
        self.VNCMessageListWidget.setEnabled(False)

        # Set Overall layout
        layout = QVBoxLayout()
        portLayout = QHBoxLayout()
        portLayout.addWidget(portLabel)
        portLayout.addWidget(self.VNCPortSpinBox)
        portLayout.addStretch()
        layout.addLayout(portLayout)
        layout.addWidget(IPLabel)
        layout.addWidget(self.VNCIPListWidget)
        layout.addWidget(self.startVNCButton)
        layout.addSpacing(15)
        layout.addWidget(messageLabel)
        layout.addWidget(self.VNCMessageListWidget)
        self.VNCGroupBox.setLayout(layout)

    def createActions(self):
        self.minimizeAction = QAction("&Start sharing", self)
        self.minimizeAction.triggered.connect(self.hide)

        self.maximizeAction = QAction("S&top sharing", self)
        self.maximizeAction.triggered.connect(self.showMaximized)
        
        self.openAction = QAction("&Open VirtScreen", self)
        self.openAction.triggered.connect(self.showNormal)

        self.quitAction = QAction("&Quit", self)
        self.quitAction.triggered.connect(QApplication.instance().quit)

    def createTrayIcon(self):
        self.trayIconMenu = QMenu(self)
        self.trayIconMenu.addAction(self.minimizeAction)
        self.trayIconMenu.addAction(self.maximizeAction)
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
                self.VNCMessageListWidget.addItem(line)
        def _onEnded(exitCode):
            self.startVNCButton.setEnabled(False)
            self.xrandr.delete_virtual_screen()
            self.isVNCRunning = False
            self.VNCMessageListWidget.setEnabled(False)
            self.startVNCButton.setText("Start VNC Server")
            self.startVNCButton.setEnabled(True)
        # Setting UI before starting
        self.VNCMessageListWidget.clear()
        self.startVNCButton.setEnabled(False)
        self.startVNCButton.setText("Running...")
        # Create virtual screen
        width = self.displayWidthSpinBox.value()
        height = self.displayHeightSpinBox.value()
        portrait = self.displayPortraitCheckBox.isChecked()
        hidpi = self.displayHIDPICheckBox.isChecked()
        position = self.displayPositionComboBox.currentData()
        self.xrandr.set_virtual_screen(width, height, portrait, hidpi)
        self.xrandr.create_virtual_screen(position)
        # Run VNC server
        self.isVNCRunning = True
        self.VNCServer = ProcessProtocol(_onReceived, _onReceived, _onEnded)
        port = self.VNCPortSpinBox.value()
        virt = self.xrandr.virt
        clip = f"{virt.width}x{virt.height}+{virt.x_offset}+{virt.y_offset}"
        arg = f"x11vnc -multiptr -repeat -rfbport {port} -clip {clip}"
        self.VNCServer.run(arg)
        # Change UI
        self.VNCMessageListWidget.setEnabled(True)
        self.startVNCButton.setEnabled(True)
        self.startVNCButton.setText("Stop")

#-------------------------------------------------------------------------------
# Main Code
#-------------------------------------------------------------------------------
if __name__ == '__main__':

    import sys

    app = QApplication(sys.argv)

    if not QSystemTrayIcon.isSystemTrayAvailable():
        QMessageBox.critical(None, "Systray",
                "I couldn't detect any system tray on this system.")
        sys.exit(1)

    if os.environ['XDG_SESSION_TYPE'] == 'wayland':
        QMessageBox.critical(None, "Wayland Session",
                            "Currently Wayland is not supported")
        sys.exit(1)

    import qt5reactor # pylint: disable=E0401
    qt5reactor.install()
    from twisted.internet import utils, reactor # pylint: disable=E0401

    QApplication.setQuitOnLastWindowClosed(False)
    window = Window()
    window.show()
    sys.exit(app.exec_())
    reactor.run()