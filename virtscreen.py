#!/usr/bin/env python

import sys, os

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import  QObject, QUrl, Qt
from PyQt5.QtCore import pyqtProperty, pyqtSlot, pyqtSignal
from PyQt5.QtGui import QIcon
from PyQt5.QtQml import qmlRegisterType, QQmlApplicationEngine

#-------------------------------------------------------------------------------
# file path definitions
#-------------------------------------------------------------------------------
PROGRAM_PATH = "."
ICON_PATH = PROGRAM_PATH + "/icon/icon.png"
ICON_TABLET_OFF_PATH = PROGRAM_PATH + "/icon/icon_tablet_off.png"
ICON_TABLET_ON_PATH = PROGRAM_PATH + "/icon/icon_tablet_on.png"

#-------------------------------------------------------------------------------
# QML Backend class
#-------------------------------------------------------------------------------
class Backend(QObject):
    width_changed = pyqtSignal(int)
    virtScreenChanged = pyqtSignal(bool)
    vncChanged = pyqtSignal(bool)

    def __init__(self, parent=None):
        super(Backend, self).__init__(parent)
        # Virtual screen properties
        self._width = 1368
        self._height = 1024
        self._portrait = True
        self._hidpi = False
        self._virtScreenCreated = False
        # VNC server properties
        self._vncPort = 5900
        self._vncPassword = ""
        self._vncState = False
    
    @pyqtProperty(int, notify=width_changed)
    def width(self):
        return self._width
    @width.setter
    def width(self, width):
        self._width = width
        self.width_changed.emit(self._width)
    
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
    def virtScreenCreated(self):
        return self._virtScreenCreated
        
    @pyqtProperty(int)
    def vncPort(self):
        return self._vncPort
    @vncPort.setter
    def vncPort(self, vncPort):
        self._vncPort = vncPort

    @pyqtProperty(str)
    def vncPassword(self):
        return self._vncPassword
    @vncPassword.setter
    def vncPassword(self, vncPassword):
        self._vncPassword = vncPassword
        print(self._vncPassword)

    # Qt Slots
    @pyqtSlot()
    def quitProgram(self):
        QApplication.instance().quit()

#-------------------------------------------------------------------------------
# Main Code
#-------------------------------------------------------------------------------
if __name__ == '__main__':
    import sys
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(ICON_PATH))
    # os.environ["QT_QUICK_CONTROLS_STYLE"] = "Material"
    os.environ["QT_QUICK_CONTROLS_STYLE"] = "Fusion"
    
    # Register the Python type.  Its URI is 'People', it's v1.0 and the type
    # will be called 'Person' in QML.
    qmlRegisterType(Backend, 'VirtScreen.Backend', 1, 0, 'Backend')

    # Create a component factory and load the QML script.
    engine = QQmlApplicationEngine()
    engine.load(QUrl('main.qml'))
    if not engine.rootObjects():
        print("Failed to load qml")
        exit(1)
    sys.exit(app.exec_())
