import QtQuick 2.10
import QtQuick.Controls 2.3
import QtQuick.Controls.Material 2.3
import QtQuick.Layouts 1.3
import QtQuick.Window 2.2

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

    width: 380
    height: 540
    property int margin: 10
    property int popupWidth: width - 26

    // hide screen when loosing focus
    property bool autoClose: true
    property bool ignoreCloseOnce: false
    onAutoCloseChanged: {
        // When setting auto close disabled and then enabled again, we need to
        // ignore focus change once. Otherwise the window always is closed one time
        // even when the mouse is clicked in the window.  
        if (!autoClose) {
            ignoreCloseOnce = true;
        }
    }
    onActiveFocusItemChanged: {
        if (autoClose && !ignoreCloseOnce && !activeFocusItem && !sysTrayIcon.clicked) {
            this.hide();
        }
        if (ignoreCloseOnce && autoClose) {
            ignoreCloseOnce = false;
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
                text: vncStateText.text
            }

            ToolButton {
                id: menuButton
                anchors.right: parent.right
                text: qsTr("⋮")
                onClicked: menu.open()

                Menu {
                    id: menu
                    y: toolbar.height

                    MenuItem {
                        text: qsTr("&About")
                        onTriggered: {
                            aboutDialog.open();
                        }
                    }

                    MenuItem {
                        text: qsTr("&Quit")
                        onTriggered: quitAction.onTriggered()
                    }
                }
            }
        }
    }

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

    // footer: ToolBar {
    //     font.weight: Font.Medium
    //     font.pointSize: 11 //parent.font.pointSize + 1
    //     anchors { horizontalCenter: parent.horizontalCenter }
    //     width: 200
    // }

    ProgressBar {
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        z: 1
        indeterminate: backend.vncState == Backend.WAITING
        value: backend.vncState == Backend.CONNECTED ? 1 : 0
    }

    Popup {
        id: busyDialog
        modal: true
        closePolicy: Popup.NoAutoClose
        x: (parent.width - width) / 2
        y: parent.height / 2 - height
        BusyIndicator {
            anchors.fill: parent
            running: true
        }
        background: Rectangle {
            color: "transparent"
            implicitWidth: 100
            implicitHeight: 100
            // border.color: "#444"
        }
    }

    Dialog {
        id: aboutDialog
        focus: true
        x: (parent.width - width) / 2
        y: (parent.width - height) / 2 //(window.height) / 2 
        width: popupWidth
        ColumnLayout {
            anchors.fill: parent
            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                horizontalAlignment: Text.AlignHCenter
                font { weight: Font.Bold; pointSize: 15 }
                text: "VirtScreen"
            }
            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                horizontalAlignment: Text.AlignHCenter
                text: "Make your iPad/tablet/computer<br/>as a secondary monitor.<br/>"
            }
            Text {
                text: "- <a href='https://github.com/kbumsik/VirtScreen'>Project Website</a>"
                onLinkActivated: Qt.openUrlExternally(link)
            }
            Text {
                text: "- <a href='https://github.com/kbumsik/VirtScreen/issues'>Issues & Bug Report</a>"
                onLinkActivated: Qt.openUrlExternally(link)
            }
            Text {
                font { pointSize: 10 }
                anchors.horizontalCenter: parent.horizontalCenter
                horizontalAlignment: Text.AlignHCenter
                lineHeight: 0.7
                text: "<br/>Copyright © 2018 Bumsik Kim  <a href='https://kbumsik.io/'>Homepage</a><br/>"
                onLinkActivated: Qt.openUrlExternally(link)
            }
            Text {
                font { pointSize: 9 }
                anchors.horizontalCenter: parent.horizontalCenter
                horizontalAlignment: Text.AlignHCenter
                text: "This program comes with absolutely no warranty.<br/>" +
                      "See the <a href='https://github.com/kbumsik/VirtScreen/blob/master/LICENSE'>" +
                      "GNU General Public License, version 3</a> for details."
                onLinkActivated: Qt.openUrlExternally(link)
            }
        }
    }

    Dialog {
        id: passwordDialog
        title: "New password"
        focus: true
        modal: true
        standardButtons: Dialog.Ok | Dialog.Cancel
        x: (parent.width - width) / 2
        y: (parent.width - height) / 2 //(window.height) / 2 
        width: popupWidth
        ColumnLayout {
            anchors.fill: parent
            TextField {
                id: passwordFIeld
                focus: true
                anchors.left: parent.left
                anchors.right: parent.right
                placeholderText: "New Password";
                echoMode: TextInput.Password;
            }
            Keys.onPressed: {
                event.accepted = true;
                if (event.key == Qt.Key_Return || event.key == Qt.Key_Enter) {
                    passwordDialog.accept();
                }
            }
        }
        onAccepted: {
            backend.createVNCPassword(passwordFIeld.text);
            passwordFIeld.text = "";
        }
        onRejected: passwordFIeld.text = ""
    }
    
    SwipeView {
        anchors.top: tabBar.bottom
        anchors.bottom: parent.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.margins: margin
        clip: true

        currentIndex: tabBar.currentIndex

        ColumnLayout {
            GroupBox {
                title: "Virtual Display"
                Layout.fillWidth: true
                enabled: backend.virtScreenCreated ? false : true
                ColumnLayout {
                    anchors.left: parent.left
                    anchors.right: parent.right
                    RowLayout {
                        Label { text: "Width"; Layout.fillWidth: true }
                        SpinBox {
                            value: settings.virt.width
                            from: 640
                            to: 1920
                            stepSize: 1
                            editable: true
                            onValueModified: {
                                settings.virt.width = value;
                            }
                            textFromValue: function(value, locale) { return value; }
                        }
                    }
                    RowLayout {
                        Label { text: "Height"; Layout.fillWidth: true }
                        SpinBox {
                            value: settings.virt.height
                            from: 360
                            to: 1080
                            stepSize : 1
                            editable: true
                            onValueModified: {
                                settings.virt.height = value;
                            }
                            textFromValue: function(value, locale) { return value; }
                        }
                    }
                    RowLayout {
                        Label { text: "Portrait Mode"; Layout.fillWidth: true }
                        Switch {
                            checked: settings.virt.portrait
                            onCheckedChanged: {
                                settings.virt.portrait = checked;
                            }
                        }
                    }
                    RowLayout {
                        Label { text: "HiDPI (2x resolution)"; Layout.fillWidth: true }
                        Switch {
                            checked: settings.virt.hidpi
                            onCheckedChanged: {
                                settings.virt.hidpi = checked;
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

            ColumnLayout {
                Layout.margins: margin / 2
                Button {
                    id: virtScreenButton
                    Layout.fillWidth: true
                    text: virtScreenAction.text
                    highlighted: true
                    enabled: virtScreenAction.enabled
                    onClicked: {
                        busyDialog.open();
                        virtScreenAction.onTriggered();
                        connectOnce(backend.onVirtScreenCreatedChanged, function(created) {
                            busyDialog.close();
                        });
                    }
                }
                Button {
                    id: displaySettingButton
                    Layout.fillWidth: true
                    text: "Open Display Setting"
                    enabled: backend.virtScreenCreated ? true : false
                    onClicked: {
                        busyDialog.open();
                        window.autoClose = false;
                        if (backend.vncState != Backend.OFF) {
                            console.log("vnc is running");
                            var restoreVNC = true;
                            if (autostart) {
                                autostart = false;
                                var restoreAutoStart = true;
                            }
                        }
                        connectOnce(backend.onDisplaySettingClosed, function() {
                            window.autoClose = true;
                            busyDialog.close();
                            if (restoreAutoStart) {
                                autostart = true;
                            }
                            if (restoreVNC) {
                                backend.startVNC(settings.vnc.port);
                            }
                        });
                        backend.stopVNC();
                        backend.openDisplaySetting();
                    }
                }      
            }

            RowLayout {
                // Empty layout
                Layout.fillHeight: true
            }
        }

        ColumnLayout {
            GroupBox {
                title: "VNC Server"
                Layout.fillWidth: true
                enabled: backend.vncState == Backend.OFF ? true : false
                ColumnLayout {
                    anchors.left: parent.left
                    anchors.right: parent.right
                    RowLayout {
                        Label { text: "Port"; Layout.fillWidth: true }
                        SpinBox {
                            value: settings.vnc.port
                            from: 1
                            to: 65535
                            stepSize: 1
                            editable: true
                            onValueModified: {
                                settings.vnc.port = value;
                            }
                            textFromValue: function(value, locale) { return value; }
                        }
                    }
                    RowLayout {
                        anchors.left: parent.left
                        anchors.right: parent.right
                        Label { text: "Password"; Layout.fillWidth: true }
                        Button {
                            text: "Delete"
                            font.capitalization: Font.MixedCase
                            highlighted: false
                            enabled: backend.vncUsePassword
                            onClicked: backend.deleteVNCPassword()
                        }
                        Button {
                            text: "New"
                            font.capitalization: Font.MixedCase
                            highlighted: true
                            enabled: !backend.vncUsePassword
                            onClicked: passwordDialog.open()
                        }
                    }
                }
            }

            RowLayout {
                Layout.fillWidth: true
                Layout.margins: margin / 2
                Button {
                    id: vncButton
                    Layout.fillWidth: true
                    text: vncAction.text
                    highlighted: true
                    enabled: vncAction.enabled
                    onClicked: vncAction.onTriggered()
                }
                CheckBox {
                    checked: autostart
                    onToggled: {
                        autostart = checked;
                        if ((checked == true) && (backend.vncState == Backend.OFF) && 
                                backend.virtScreenCreated) {
                            backend.startVNC(settings.vnc.port);
                        }
                    }
                }
                Label { text: "Auto"; }
            }

            GroupBox {
                title: "Available IP addresses"
                Layout.fillWidth: true
                implicitHeight: 150
                ColumnLayout {
                    anchors.fill: parent
                    ListView {
                        id: ipListView
                        anchors.fill: parent
                        clip: true
                        ScrollBar.vertical: ScrollBar {
                            parent: ipListView.parent
                            anchors.top: ipListView.top
                            anchors.right: ipListView.right
                            anchors.bottom: ipListView.bottom
                            policy: ScrollBar.AlwaysOn
                        }
                        model: backend.ipAddresses
                        delegate: TextEdit {
                            text: modelData
                            readOnly: true
                            selectByMouse: true
                            anchors.horizontalCenter: parent.horizontalCenter
                            font.pointSize: 12
                        }
                    }
                }
            }

            RowLayout {
                // Empty layout
                Layout.fillHeight: true
            }
        }
    }
}
