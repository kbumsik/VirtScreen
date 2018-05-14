import QtQuick 2.10

import Qt.labs.platform 1.0

import VirtScreen.DisplayProperty 1.0
import VirtScreen.Backend 1.0

Item {
    property alias window: mainLoader.item
    
    // virtscreen.py backend.
    Backend {
        id: backend
        function switchVNC () {
            if ((backend.vncState == Backend.OFF) && backend.virtScreenCreated) {
                backend.startVNC();
            }
        }
        onVncAutoStartChanged: {
            if (vncAutoStart) {
                onVirtScreenCreatedChanged.connect(switchVNC);
                onVncStateChanged.connect(switchVNC);
            } else {
                onVirtScreenCreatedChanged.disconnect(switchVNC);
                onVncStateChanged.disconnect(switchVNC);
            }
        }
        Component.onCompleted: {
            // force emit signal on load 
            vncAutoStart = vncAutoStart;
        }
    }

    // Timer object and function
    Timer {
        id: timer
        function setTimeout(cb, delayTime) {
            timer.interval = delayTime;
            timer.repeat = false;
            timer.triggered.connect(cb);
            timer.triggered.connect(function() {
                timer.triggered.disconnect(cb);
            });
            timer.start();
        }
    }

    // One-shot signal connect
    function connectOnce (signal, slot) {
        var f = function() {
            slot.apply(this, arguments);
            signal.disconnect(f);
        }
        signal.connect(f);
    }

    Loader {
        id: mainLoader
        active: false
        source: "mainWindow.qml"

        onStatusChanged: {
            console.log("Loader Status Changed.", status);
            if (status == Loader.Null) {
                gc();
                // This cause memory leak at this moment.
                // backend.clearCache();
            }
        }

        onLoaded: {
            window.onVisibleChanged.connect(function(visible) {
                if (!visible) {
                    console.log("Unloading ApplicationWindow...");
                    mainLoader.active = false;
                }
            });
            // Move window to the corner of the primary display
            var primary = backend.primary;
            var width = primary.width;
            var height = primary.height;
            var cursor_x = backend.cursor_x - primary.x_offset;
            var cursor_y = backend.cursor_y - primary.y_offset;
            var x_mid = width / 2;
            var y_mid = height / 2;
            var x = width - window.width; //(cursor_x > x_mid)? width - window.width : 0;
            var y = (cursor_y > y_mid)? height - window.height : 0;
            x += primary.x_offset;
            y += primary.y_offset;
            window.x = x;
            window.y = y;
            window.show();
            window.raise();
            window.requestActivate();
            timer.setTimeout (function() {
                sysTrayIcon.clicked = false;
            }, 200);
        }
    }

    // Sytray Icon
    SystemTrayIcon {
        id: sysTrayIcon
        iconSource: backend.vncState == Backend.CONNECTED ? "icon/icon_tablet_on.png" :
                    backend.virtScreenCreated ? "icon/icon_tablet_off.png" :
                    "icon/icon.png"
        visible: true
        property bool clicked: false
        onMessageClicked: console.log("Message clicked")
        Component.onCompleted: {
            // without delay, the message appears in a wierd place 
            timer.setTimeout (function() {
                showMessage("VirtScreen is running",
                    "The program will keep running in the system tray.\n" +
                    "To terminate the program, choose \"Quit\" in the \n" +
                    "context menu of the system tray entry.");
            }, 1500);
        }

        onActivated: function(reason) {
            if (reason == SystemTrayIcon.Context) {
                return;
            }
            sysTrayIcon.clicked = true;
            mainLoader.active = true;
        }

        menu: Menu {
            MenuItem {
                id: vncStateText
                text: !backend.virtScreenCreated ? "Enable Virtual Screen first." :
                      backend.vncState == Backend.OFF ? "Turn on VNC Server in the VNC tab." :
                      backend.vncState == Backend.WAITING ? "VNC Server is waiting for a client..." :
                      backend.vncState == Backend.CONNECTED ? "Connected." :
                      "Server state error!"
            }
            MenuItem {
                separator: true
            }
            MenuItem {
                id: virtScreenAction
                text: backend.virtScreenCreated ? "Disable Virtual Screen" : "Enable Virtual Screen"
                enabled:backend.vncAutoStart ? true :
                        backend.vncState == Backend.OFF ? true : false
                onTriggered: {
                    // Give a very short delay to show busyDialog.
                    timer.setTimeout (function() {
                        if (!backend.virtScreenCreated) {
                            backend.createVirtScreen();
                        } else {
                            // If auto start enabled, stop VNC first then 
                            if (backend.vncAutoStart && (backend.vncState != Backend.OFF)) {
                                backend.vncAutoStart = false;
                                connectOnce(backend.onVncStateChanged, function() {
                                    console.log("autoOff called here", backend.vncState);
                                    if (backend.vncState == Backend.OFF) {
                                        console.log("Yes. Delete it");
                                        backend.deleteVirtScreen();
                                        backend.vncAutoStart = true;
                                    }
                                });
                                backend.stopVNC();
                            } else {
                                backend.deleteVirtScreen();
                            }
                        }
                    }, 200);
                }
            }
            MenuItem {
                id: vncAction
                text: backend.vncAutoStart ? "Auto start enabled" : 
                      backend.vncState == Backend.OFF ? "Start VNC Server" : "Stop VNC Server"
                enabled: backend.vncAutoStart ? false : 
                         backend.virtScreenCreated ? true : false
                onTriggered: backend.vncState == Backend.OFF ? backend.startVNC() : backend.stopVNC()
            }
            MenuItem {
                separator: true
            }
            MenuItem {
                text: qsTr("&Quit")
                onTriggered: {
                    backend.quitProgram();
                }
            }
        }
    }
}