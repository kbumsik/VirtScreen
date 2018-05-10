import QtQuick 2.10
import QtQuick.Controls 2.3
import QtQuick.Controls.Material 2.3
import QtQuick.Layouts 1.3
import QtQuick.Window 2.2

import Qt.labs.platform 1.0 as Labs

import VirtScreen.DisplayProperty 1.0
import VirtScreen.Backend 1.0


ApplicationWindow {
    id: window
    visible: false
    flags: Qt.FramelessWindowHint
    title: "Basic layouts"

    Material.theme: Material.Light
    Material.accent: Material.Teal

    property int margin: 11
    width: 380
    height: 600

    // hide screen when loosing focus
    onActiveFocusItemChanged: {
        if ((!activeFocusItem) && (!sysTrayIcon.clicked)) {
            this.hide();
        }
    }

    // virtscreen.py backend.
    Backend {
        id: backend
    }

    DisplayProperty {
        id: display
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
                            value: backend.virt.width
                            from: 640
                            to: 1920
                            stepSize: 1
                            editable: true
                            onValueModified: {
                                backend.virt.width = value;
                            }
                        }
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        Label { text: "Height"; Layout.fillWidth: true }
                        SpinBox {
                            value: backend.virt.height
                            from: 360
                            to: 1080
                            stepSize : 1
                            editable: true
                            onValueModified: {
                                backend.virt.height = value;
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

                    RowLayout {
                        Layout.fillWidth: true
                        Label { text: "Device"; Layout.fillWidth: true }
                        ComboBox {
                            id: deviceComboBox
                            textRole: "name"
                            model: []
                            
                            Component.onCompleted: {
                                var screens = backend.screens;
                                var list = [];
                                for (var i = 0; i < screens.length; i++) {
                                    list.push(screens[i]);
                                }
                                deviceComboBox.model = list;
                            }
                            delegate: ItemDelegate {
                                width: deviceComboBox.width
                                text: modelData.name
                                font.weight: deviceComboBox.currentIndex === index ? Font.DemiBold : Font.Normal
                                highlighted: ListView.isCurrentItem
                                enabled: modelData.connected? false: true
                            }
                        }
                    }
                }
            }

            Button {
                id: virtScreenButton
                text: "Enable Virtual Screen"
                Layout.fillWidth: true
                // Material.background: Material.Teal
                // Material.foreground: Material.Grey

                Popup {
                    id: busyDialog
                    modal: true
                    closePolicy: Popup.NoAutoClose

                    x: (parent.width - width) / 2
                    y: (parent.height - height) / 2

                    BusyIndicator {
                        x: (parent.width - width) / 2
                        y: (parent.height - height) / 2
                        running: true
                    }
                }

                onClicked: {
                    virtScreenButton.enabled = false;
                    busyDialog.open();
                    // Give a very short delay to show busyDialog.
                    timer.setTimeout (function() {
                        if (!backend.virtScreenCreated) {
                            backend.createVirtScreen();
                        } else {
                            backend.deleteVirtScreen();
                        }
                    }, 200);
                }

                Component.onCompleted: {
                    backend.onVirtScreenCreatedChanged.connect(function(created) {
                        busyDialog.close();
                        virtScreenButton.enabled = true;
                        if (created) {
                            virtScreenButton.text = "Disable Virtual Screen"
                        } else {
                            virtScreenButton.text = "Enable Virtual Screen"
                        }
                    });
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
                id: vncButton
                text: "Start VNC Server"
                enabled: false
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

                Component.onCompleted: {
                    backend.onVncStateChanged.connect(function(state) {
                        if (state == "Off") {
                            vncButton.text = "Start VNC Server";
                        } else {
                            vncButton.text = "Stop VNC Server";
                        }
                    });
                    backend.onVirtScreenCreatedChanged.connect(function(created) {
                        if (created) {
                            vncButton.enabled = true;
                        } else {
                            vncButton.enabled = false;
                        }
                    });
                }
            }
        }
    }

    footer: ToolBar {
        RowLayout {
            anchors.margins: spacing
            Label {
                id: vncStateLabel
                text: backend.vncState
            }
            Item { Layout.fillWidth: true }
            CheckBox {
                id: enabler
                text: "Server Enabled"
                checked: true
            }
        }

        Component.onCompleted: {
            backend.onVncStateChanged.connect(function(state) {
                vncStateLabel.text = state;
            });
        }
    }

    // Sytray Icon
    Labs.SystemTrayIcon {
        id: sysTrayIcon
        iconSource: "icon/icon.png"
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
            console.log(reason);
            if (reason == Labs.SystemTrayIcon.Context) {
                return;
            }
            if (window.visible) {
                window.hide();
                return;
            }
            sysTrayIcon.clicked = true;
            // Move window to the corner of the primary display
            var primary = backend.primary;
            var width = primary.width;
            var height = primary.height;
            var x_mid = width / 2;
            var y_mid = height / 2;
            window.x = width - window.width; //(backend.cursor_x > x_mid)? width - window.width : 0;
            window.y = (backend.cursor_y > y_mid)? height - window.height : 0;
            window.show();
            window.raise();
            window.requestActivate();
            timer.setTimeout (function() {
                sysTrayIcon.clicked = false;
            }, 200);
        }

        menu: Labs.Menu {
            Labs.MenuItem {
                text: qsTr("&Quit")
                onTriggered: backend.quitProgram()
            }
        }
    }
}
