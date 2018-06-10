import QtQuick 2.10

import Qt.labs.platform 1.0

import VirtScreen.DisplayProperty 1.0
import VirtScreen.Backend 1.0
import VirtScreen.Cursor 1.0

Item {
    property alias window: mainLoader.item
    property var settings: JSON.parse(backend.settings)
    property bool autostart: settings.vnc.autostart

    function saveSettings () {
        settings.vnc.autostart = autostart;
        backend.settings = JSON.stringify(settings, null, 4);
    }

    function createVirtScreen () {
        backend.createVirtScreen(settings.virt.device, settings.virt.width,
                                settings.virt.height, settings.virt.portrait,
                                settings.virt.hidpi);
    }

    function startVNC () {
        saveSettings();
        backend.startVNC(settings.vnc.port);
    }

    function stopVNC () {
        backend.stopVNC();
    }

    function switchVNC () {
        if ((backend.vncState == Backend.OFF) && backend.virtScreenCreated) {
            startVNC();
        }
    }

    onAutostartChanged: {
        if (autostart) {
            backend.onVirtScreenCreatedChanged.connect(switchVNC);
            backend.onVncStateChanged.connect(switchVNC);
        } else {
            backend.onVirtScreenCreatedChanged.disconnect(switchVNC);
            backend.onVncStateChanged.disconnect(switchVNC);
        }
    }

    // virtscreen.py backend.
    Backend {
        id: backend
        onVncStateChanged: {
            if (backend.vncState == Backend.ERROR) {
                autostart = false;
            }
        }
    }

    // virtscreen.py Cursor class.
    Cursor {
        id: cursor
    }

    // Timer object and function
    Timer {
        id: timer
        function setTimeout(cb, delayTime) {
            if (timer.running) {
                console.log('Timer is already running!');
            }
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
        source: "AppWindow.qml"

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
            var cursor_x = (cursor.x / window.screen.devicePixelRatio) - window.screen.virtualX;
            var cursor_y = (cursor.y / window.screen.devicePixelRatio) - window.screen.virtualY;
            var x_mid = window.screen.width / 2;
            var y_mid = window.screen.height / 2;
            var x = window.screen.width - window.width; //(cursor_x > x_mid)? width - window.width : 0;
            var y = (cursor_y > y_mid)? window.screen.height - window.height : 0;
            x += window.screen.virtualX;
            y += window.screen.virtualY;
            window.x = x;
            window.y = y;
            window.show();
            window.raise();
            window.requestActivate();
        }
    }

    // Sytray Icon
    SystemTrayIcon {
        id: sysTrayIcon
        iconSource: backend.vncState == Backend.CONNECTED ? "../icon/icon_tablet_on.png" :
                    backend.virtScreenCreated ? "../icon/icon_tablet_off.png" :
                    "../icon/icon.png"
        visible: true
        property bool clicked: false
        
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
            timer.setTimeout (function() {
                sysTrayIcon.clicked = false;
            }, 200);
            mainLoader.active = true;
        }

        menu: Menu {
            MenuItem {
                id: vncStateText
                text: !backend.virtScreenCreated ? "Enable Virtual Screen first" :
                      backend.vncState == Backend.OFF ? "Turn on VNC Server in the VNC tab" :
                      backend.vncState == Backend.ERROR ? "Error occurred" :
                      backend.vncState == Backend.WAITING ? "VNC Server is waiting for a client..." :
                      backend.vncState == Backend.CONNECTED ? "Connected" :
                      "Server state error!"
            }
            MenuItem {
                id: errorText
                visible: (text)
                text: ""
                Component.onCompleted : {
                    backend.onError.connect(function(errMsg) {
                        errorText.text = "";    // To trigger onTextChanged signal
                        errorText.text = errMsg;
                    });
                }
            }
            MenuItem {
                separator: true
            }
            MenuItem {
                id: virtScreenAction
                text: backend.virtScreenCreated ? "Disable Virtual Screen" : "Enable Virtual Screen"
                enabled: autostart ? true :
                         backend.vncState == Backend.OFF ? true : false
                onTriggered: {
                    // Give a very short delay to show busyDialog.
                    timer.setTimeout (function() {
                        if (!backend.virtScreenCreated) {
                            createVirtScreen();
                        } else {
                            // If auto start enabled, stop VNC first then 
                            if (autostart && (backend.vncState != Backend.OFF)) {
                                autostart = false;
                                connectOnce(backend.onVncStateChanged, function() {
                                    console.log("autoOff called here", backend.vncState);
                                    if (backend.vncState == Backend.OFF) {
                                        console.log("Yes. Delete it");
                                        backend.deleteVirtScreen();
                                        autostart = true;
                                    }
                                });
                                stopVNC();
                            } else {
                                backend.deleteVirtScreen();
                            }
                        }
                    }, 200);
                }
            }
            MenuItem {
                id: vncAction
                text: autostart ? "Auto start enabled" : 
                      backend.vncState == Backend.OFF ? "Start VNC Server" : "Stop VNC Server"
                enabled: autostart ? false : 
                         backend.virtScreenCreated ? true : false
                onTriggered: backend.vncState == Backend.OFF ? startVNC() : stopVNC()
            }
            MenuItem {
                separator: true
            }
            MenuItem {
                text: "Open VirtScreen"
                onTriggered: sysTrayIcon.onActivated(SystemTrayIcon.Trigger)
            }
            MenuItem {
                id: quitAction
                text: qsTr("&Quit")
                onTriggered: {
                    saveSettings();
                    backend.quitProgram();
                }
            }
        }
    }
}