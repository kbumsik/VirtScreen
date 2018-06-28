"""Display information data classes"""

from PyQt5.QtCore import QObject, pyqtProperty


class Display(object):
    """Display information"""
    __slots__ = ['name', 'primary', 'connected', 'active', 'width', 'height',
                 'x_offset', 'y_offset']

    def __init__(self):
        self.name: str = None
        self.primary: bool = False
        self.connected: bool = False
        self.active: bool = False
        self.width: int = 0
        self.height: int = 0
        self.x_offset: int = 0
        self.y_offset: int = 0

    def __str__(self) -> str:
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
    """Wrapper around Display class for Qt"""
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
