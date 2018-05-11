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
    Material.primary: Material.Teal
    Material.accent: Material.Teal
    // Material.background: Material.Grey

    property int margin: 11
    width: 380
    height: 550

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
    property bool vncAutoStart: false

    function switchVNC () {
        if ((backend.vncState == Backend.OFF) && backend.virtScreenCreated) {
            backend.startVNC();
        }
    }
    
    onVncAutoStartChanged: {
        if (vncAutoStart) {
            backend.onVirtScreenCreatedChanged.connect(switchVNC);
            backend.onVncStateChanged.connect(switchVNC);
        } else {
            backend.onVirtScreenCreatedChanged.disconnect(switchVNC);
            backend.onVncStateChanged.disconnect(switchVNC);
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

    // menuBar: MenuBar {
    // }

    header: TabBar {
        id: tabBar
        position: TabBar.Footer
        // Material.primary: Material.Teal

        currentIndex: 0

        TabButton {
            text: qsTr("Display")
        }

        TabButton {
            text: qsTr("VNC")
        }
    }

    menuBar: ToolBar {
        id: toolbar
        font.weight: Font.Medium
        font.pointSize: 11 //parent.font.pointSize + 1

        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: margin + 10
            
            Label {
                id: vncStateLabel
                text: !backend.virtScreenCreated ? "Enable Virtual Screen first." :
                      backend.vncState == Backend.OFF ? "Turn on VNC Server in the VNC tab." :
                      backend.vncState == Backend.WAITING ? "VNC Server is waiting for a client..." :
                      backend.vncState == Backend.CONNECTED ? "Connected." :
                      "Server state error!"
            }
        }
    }

    // footer: ToolBar {
    //     font.weight: Font.Medium
    //     font.pointSize: 11 //parent.font.pointSize + 1
    //     anchors { horizontalCenter: parent.horizontalCenter }
    //     width: 200
    // }

    Popup {
        id: busyDialog
        modal: true
        closePolicy: Popup.NoAutoClose

        x: (parent.width - width) / 2
        y: (parent.height - height) / 2

        BusyIndicator {
            anchors.fill: parent
            Material.accent: Material.Cyan
            running: true
        }

        background: Rectangle {
            color: "transparent"
            implicitWidth: 100
            implicitHeight: 100
            // border.color: "#444"
        }
    }

    StackLayout {
        width: parent.width
        currentIndex: tabBar.currentIndex

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: margin
            
            GroupBox {
                title: "Virtual Display"
                // font.bold: true
                anchors.left: parent.left
                anchors.right: parent.right

                enabled: backend.virtScreenCreated ? false : true
                
                ColumnLayout {
                    anchors.left: parent.left
                    anchors.right: parent.right

                    RowLayout {
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
                            textFromValue: function(value, locale) { return value; }
                        }
                    }

                    RowLayout {
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
                            textFromValue: function(value, locale) { return value; }
                        }
                    }

                    RowLayout {
                        Label { text: "Portrait Mode"; Layout.fillWidth: true }
                        Switch {
                            checked: backend.portrait
                            onCheckedChanged: {
                                backend.portrait = checked;
                            }
                        }
                    }

                    RowLayout {
                        Label { text: "HiDPI (2x resolution)"; Layout.fillWidth: true }
                        Switch {
                            checked: backend.hidpi
                            onCheckedChanged: {
                                backend.hidpi = checked;
                            }
                        }
                    }

                    RowLayout {
                        anchors.left: parent.left
                        anchors.right: parent.right

                        Label { id: deviceLabel; text: "Device"; }
                        ComboBox {
                            id: deviceComboBox
                            anchors.left: deviceLabel.right
                            anchors.right: parent.right
                            anchors.leftMargin: 100

                            textRole: "name"
                            model: backend.screens
                            currentIndex: backend.virtScreenIndex

                            onActivated: function(index) {
                                backend.virtScreenIndex = index
                            } 

                            delegate: ItemDelegate {
                                width: deviceComboBox.width
                                text: modelData.name
                                font.weight: deviceComboBox.currentIndex === index ? Font.DemiBold : Font.Normal
                                highlighted: ListView.isCurrentItem
                                enabled: modelData.connected ? false : true
                            }
                        }
                    }
                }
            }

            Button {
                id: virtScreenButton
                text: backend.virtScreenCreated ? "Disable Virtual Screen" : "Enable Virtual Screen"
                highlighted: true
                
                anchors.left: parent.left
                anchors.right: parent.right
                // Material.accent: Material.Teal
                // Material.theme: Material.Dark

                enabled: window.vncAutoStart ? true :
                         backend.vncState == Backend.OFF ? true : false

                onClicked: {
                    busyDialog.open();
                    // Give a very short delay to show busyDialog.
                    timer.setTimeout (function() {
                        if (!backend.virtScreenCreated) {
                            backend.createVirtScreen();
                        } else {
                            function autoOff() {
                                console.log("autoOff called here", backend.vncState);
                                if (backend.vncState == Backend.OFF) {
                                    console.log("Yes. Delete it");
                                    backend.deleteVirtScreen();
                                    window.vncAutoStart = true;
                                }
                            }

                            if (window.vncAutoStart && (backend.vncState != Backend.OFF)) {
                                window.vncAutoStart = false;
                                backend.onVncStateChanged.connect(autoOff);
                                backend.onVncStateChanged.connect(function() {
                                    backend.onVncStateChanged.disconnect(autoOff);
                                });
                                backend.stopVNC();
                            } else {
                                backend.deleteVirtScreen();
                            }
                        }
                    }, 200);
                }

                Component.onCompleted: {
                    backend.onVirtScreenCreatedChanged.connect(function(created) {
                        busyDialog.close();
                    });
                }
            }
        }

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: margin

            GroupBox {
                title: "VNC Server"
                anchors.left: parent.left
                anchors.right: parent.right

                enabled: backend.vncState == Backend.OFF ? true : false

                ColumnLayout {
                    anchors.left: parent.left
                    anchors.right: parent.right

                    RowLayout {
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
                            textFromValue: function(value, locale) { return value; }
                        }
                    }

                    RowLayout {
                        anchors.left: parent.left
                        anchors.right: parent.right

                        Label { id: passwordLabel; text: "Password" }
                        TextField {
                            anchors.left: passwordLabel.right
                            anchors.right: parent.right
                            anchors.margins: margin

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
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.bottomMargin: 0
                highlighted: true

                text: window.vncAutoStart ? "Auto start enabled" : 
                      backend.vncState == Backend.OFF ? "Start VNC Server" : "Stop VNC Server"
                enabled: window.vncAutoStart ? false : 
                         backend.virtScreenCreated ? true : false
                // Material.background: Material.Teal
                // Material.foreground: Material.Grey
                onClicked: backend.vncState == Backend.OFF ? backend.startVNC() : backend.stopVNC()
            }

            RowLayout {
                anchors.top: vncButton.top
                anchors.right: parent.right
                anchors.topMargin: vncButton.height - 10

                Label { text: "Auto start"; }
                Switch {
                    checked: window.vncAutoStart
                    onCheckedChanged: {
                        if ((checked == true) && (backend.vncState == Backend.OFF) && 
                                backend.virtScreenCreated) {
                            backend.startVNC();
                        }
                        window.vncAutoStart = checked;
                    }
                }
            }

            ListView {
                id: ipListView
                height: 200
                anchors.left: parent.left
                anchors.right: parent.right

                model: backend.ipAddresses
                delegate: Text {
                    text: modelData
                }
            }
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

        menu: Labs.Menu {
            Labs.MenuItem {
                text: qsTr("&Quit")
                onTriggered: {
                    backend.onVirtScreenCreatedChanged.disconnect(window.switchVNC);
                    backend.onVncStateChanged.disconnect(window.switchVNC);
                    backend.quitProgram();
                }
            }
        }
    }
}
