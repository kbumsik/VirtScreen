"""XRandr parser"""

import re
import atexit
import subprocess
import logging
from typing import List

from .display import Display
from .process import SubprocessWrapper


VIRT_SCREEN_SUFFIX = "_virt"


class XRandR(SubprocessWrapper):
    """XRandr parser class"""

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
        logging.info("Display information:")
        for s in self.screens:
            logging.info(f"\t{s}")
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
        self.mode_name = str(self.virt.width) + "x" + str(self.virt.height) + VIRT_SCREEN_SUFFIX
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
        logging.info(f"creating: {self.virt}")
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
