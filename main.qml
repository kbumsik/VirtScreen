import QtQuick 2.10
import QtQuick.Controls 2.3
// import QtQuick.Controls.Material 2.3
import QtQuick.Layouts 1.3
import QtQuick.Window 2.2

import Qt.labs.platform 1.0 as Labs

import VirtScreen.Backend 1.0


ApplicationWindow {
    id: window
    visible: false
    flags: Qt.FramelessWindowHint
    title: "Basic layouts"

    // Material.theme: Material.Light
    // Material.accent: Material.Teal

    property int margin: 11
    width: 380
    height: 600

    // hide screen when loosing focus
    onActiveFocusItemChanged: {
        if (!activeFocusItem) {
            this.hide();
        }
    }

    // virtscreen.py hackend.
    Backend {
        id: backend
    }

    // Timer object and function
    Timer {
        id: timer
        function setTimeout(cb, delayTime) {
            timer.interval = delayTime;
            timer.repeat = false;
            timer.triggered.connect(cb);
            timer.start();
        }
    }

    header: TabBar {
        id: tabBar
        position: TabBar.Header
        width: parent.width
        currentIndex: 0

        TabButton {
            text: qsTr("Display")
        }

        TabButton {
            text: qsTr("VNC")
        }
    }

    StackLayout {
        width: parent.width
        currentIndex: tabBar.currentIndex

        ColumnLayout {
            // enabled: enabler.checked
            // anchors.top: parent.top
            // anchors.left: parent.left
            // anchors.right: parent.right
            // anchors.margins: margin
            
            GroupBox {
                title: "Virtual Display"
                // font.bold: true
                Layout.fillWidth: true
                
                ColumnLayout {
                    Layout.fillWidth: true

                    RowLayout {
                        Layout.fillWidth: true
                        Label { text: "Width"; Layout.fillWidth: true }
                        SpinBox {
                            value: backend.width
                            from: 640
                            to: 1920
                            stepSize: 1
                            editable: true
                            textFromValue: function(value, locale) {
                                return Number(value).toLocaleString(locale, 'f', 0) + " px";
                            }
                            onValueModified: {
                                backend.width = value;
                            }
                        }
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        Label { text: "Height"; Layout.fillWidth: true }
                        SpinBox {
                            value: backend.height
                            from: 360
                            to: 1080
                            stepSize : 1
                            editable: true
                            textFromValue: function(value, locale) {
                                return Number(value).toLocaleString(locale, 'f', 0) + " px";
                            }
                            onValueModified: {
                                backend.height = value;
                            }
                        }
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        Label { text: "Portrait Mode"; Layout.fillWidth: true }
                        Switch {
                            checked: backend.portrait
                            onCheckedChanged: {
                                backend.portrait = checked;
                            }
                        }
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        Label { text: "HiDPI (2x resolution)"; Layout.fillWidth: true }
                        Switch {
                            checked: backend.hidpi
                            onCheckedChanged: {
                                backend.hidpi = checked;
                            }
                        }
                    }
                }
            }

            Button {
                text: "Create a Virtual Display"
                Layout.fillWidth: true
                // Material.background: Material.Teal
                // Material.foreground: Material.Grey
                onClicked: {
                    if (!backend.virtScreenCreated) {
                        backend.createVirtScreen();
                    } else {
                        backend.deleteVirtScreen();
                    }
                }
            }
        }

        ColumnLayout {
            // enabled: enabler.checked
            // anchors.top: parent.top
            // anchors.left: parent.left
            // anchors.right: parent.right
            // anchors.margins: margin

            GroupBox {
                title: "VNC Server"
                Layout.fillWidth: true
                // Layout.fillWidth: true
                ColumnLayout {
                    Layout.fillWidth: true

                    RowLayout {
                        Layout.fillWidth: true
                        Label { text: "Port"; Layout.fillWidth: true }
                        SpinBox {
                            value: backend.vncPort
                            from: 1
                            to: 65535
                            stepSize: 1
                            editable: true
                            onValueModified: {
                                backend.vncPort = value;
                            }
                        }
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        Label { text: "Password" }
                        TextField {
                            Layout.fillWidth: true
                            placeholderText: "Password";
                            text: backend.vncPassword;
                            echoMode: TextInput.Password;
                            onTextEdited: {
                                backend.vncPassword = text;
                            }
                        }
                    }
                }
            }

            Button {
                text: "Start VNC Server"
                Layout.fillWidth: true
                // Material.background: Material.Teal
                // Material.foreground: Material.Grey
                onClicked: {
                    if (backend.vncState == 'Off') {
                        backend.startVNC()
                    } else {
                        backend.stopVNC()
                    }
                }
            }
        }
    }

    footer: ToolBar {
        RowLayout {
            anchors.margins: spacing
            Label {
                text: backend.vncState
            }
            Item { Layout.fillWidth: true }
            CheckBox {
                id: enabler
                text: "Server Enabled"
                checked: true
            }
        }
    }

    // Sytray Icon
    Labs.SystemTrayIcon {
        id: sysTrayIcon
        iconSource: "icon/icon.png"
        visible: true

        onMessageClicked: console.log("Message clicked")
        Component.onCompleted: {
            // without delay, the message appears in a wierd place 
            timer.setTimeout (function() {
                showMessage("Message title", "Something important came up. Click this to know more.");
            }, 1000);
        }

        onActivated: {
            if (window.visible) {
                window.hide();
                return;
            }
            // Move window to the corner of the primary display
            var width = backend.primaryDisplayWidth;
            var height = backend.primaryDisplayHeight;
            var x_mid = width / 2;
            var y_mid = height / 2;
            window.x = (backend.cursor_x > x_mid)? width - window.width : 0;
            window.y = (backend.cursor_y > y_mid)? height - window.height : 0;
            window.show()
            window.raise()
            window.requestActivate()
        }

        menu: Labs.Menu {
            Labs.MenuItem {
                text: qsTr("&Quit")
                onTriggered: backend.quitProgram()
            }
        }
    }
}
