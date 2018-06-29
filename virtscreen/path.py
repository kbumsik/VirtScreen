"""File path definitions"""

import os
from pathlib import Path


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
ICON_PATH = BASE_PATH + "/icon/full_256x256.png"
ASSETS_PATH = BASE_PATH + "/assets"
DATA_PATH = ASSETS_PATH + "/data.json"
DEFAULT_CONFIG_PATH = ASSETS_PATH + "/config.default.json"
MAIN_QML_PATH = ASSETS_PATH + "/main.qml"
