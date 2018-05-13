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
    height: 525
    property int margin: 8
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
                        onTriggered: {
                            backend.quitProgram();
                        }
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

    Popup {
        id: busyDialog
        modal: true
        closePolicy: Popup.NoAutoClose
        x: (parent.width - width) / 2
        y: parent.height / 2 - height
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

    StackLayout {
        width: parent.width
        anchors.top: tabBar.bottom
        anchors.bottom: parent.bottom

        currentIndex: tabBar.currentIndex

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: margin
            GroupBox {
                title: "Virtual Display"
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
                text: virtScreenAction.text
                highlighted: true
                anchors.left: parent.left
                anchors.right: parent.right
                // Material.accent: Material.Teal
                // Material.theme: Material.Dark
                enabled: virtScreenAction.enabled
                onClicked: {
                    busyDialog.open();
                    virtScreenAction.onTriggered();
                }
                Component.onCompleted: {
                    backend.onVirtScreenCreatedChanged.connect(function(created) {
                        busyDialog.close();
                    });
                }
            }
            Button {
                id: displaySettingButton
                text: "Open Display Setting"
                anchors.left: parent.left
                anchors.right: parent.right
                // Material.accent: Material.Teal
                // Material.theme: Material.Dark
                enabled: backend.virtScreenCreated ? true : false
                onClicked: {
                    busyDialog.open();
                    window.autoClose = false;
                    if (backend.vncState != Backend.OFF) {
                        console.log("vnc is running");
                        var restoreVNC = true;
                        if (backend.vncAutoStart) {
                            backend.vncAutoStart = false;
                            var restoreAutoStart = true;
                        }
                    }
                    connectOnce(backend.onDisplaySettingClosed, function() {
                        window.autoClose = true;
                        busyDialog.close();
                        if (restoreAutoStart) {
                            backend.vncAutoStart = true;
                        }
                        if (restoreVNC) {
                            backend.startVNC();
                        }
                    });
                    backend.stopVNC();
                    backend.openDisplaySetting();
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
            Button {
                id: vncButton
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.bottomMargin: 0
                highlighted: true
                text: vncAction.text
                enabled: vncAction.enabled
                // Material.background: Material.Teal
                // Material.foreground: Material.Grey
                onClicked: vncAction.onTriggered()
            }
            RowLayout {
                id: autoSwitchLayout
                anchors.top: vncButton.top
                anchors.right: parent.right
                anchors.topMargin: vncButton.height - 10
                Label { text: "Auto start"; }
                Switch {
                    checked: backend.vncAutoStart
                    onToggled: {
                        if ((checked == true) && (backend.vncState == Backend.OFF) && 
                                backend.virtScreenCreated) {
                            backend.startVNC();
                        }
                        backend.vncAutoStart = checked;
                    }
                }
            }
            GroupBox {
                title: "Available IP addresses"
                anchors.top: autoSwitchLayout.bottom
                anchors.bottom: parent.bottom
                anchors.left: parent.left
                anchors.right: parent.right
                ColumnLayout {
                    anchors.fill: parent
                    ListView {
                        id: ipListView
                        anchors.fill: parent
                        // anchors.top: parent.top
                        // anchors.left: parent.left
                        // anchors.right: parent.right
                        // height: 100
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
        }
    }
}
