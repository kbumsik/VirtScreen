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

    property int theme_color: settings.theme_color
    Material.theme: Material.Light
    Material.primary: theme_color
    Material.accent: theme_color
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
                color: "white"
                text: vncStateText.text
            }

            ToolButton {
                id: menuButton
                anchors.right: parent.right
                text: qsTr("⋮")
                contentItem: Text {
                    text: parent.text
                    font: parent.font
                    color: "white"
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                    elide: Text.ElideRight
                }

                onClicked: menu.open()

                Menu {
                    id: menu
                    y: toolbar.height

                    MenuItem {
                        text: qsTr("&Preference")
                        onTriggered: {
                            preferenceLoader.active = true;
                        }
                    }

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

    footer: ProgressBar {
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

    Dialog {
        id: errorDialog
        title: "Error"
        focus: true
        modal: true
        standardButtons: Dialog.Ok
        x: (parent.width - width) / 2
        y: (parent.width - height) / 2 //(window.height) / 2 
        width: popupWidth
        height: 310
        ColumnLayout {
            anchors.fill: parent
            ScrollView {
                anchors.fill: parent
                TextArea {
                    // readOnly: true
                    selectByMouse: true
                    Layout.fillWidth: true
                    // wrapMode: Text.WordWrap
                    text: errorText.text
                    onTextChanged: {
                        if (text) {
                            busyDialog.close();
                            errorDialog.open();
                        }
                    }
                }
                ScrollBar.vertical: ScrollBar {
                    // parent: ipListView.parent
                    anchors.top: parent.top
                    anchors.left: parent.right
                    anchors.bottom: parent.bottom
                    policy: ScrollBar.AlwaysOn
                }
                ScrollBar.horizontal: ScrollBar {
                    // parent: ipListView.parent
                    anchors.top: parent.bottom
                    anchors.left: parent.left
                    anchors.right: parent.right
                    policy: ScrollBar.AlwaysOn
                }
            }
        }
    }

    Loader {
        id: preferenceLoader
        active: false
        source: "preferenceDialog.qml"
        onLoaded: {
            item.onClosed.connect(function() {
                preferenceLoader.active = false;
            });
        }
    }
    
    SwipeView {
        anchors.top: tabBar.bottom
        anchors.bottom: parent.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.margins: margin
        clip: true

        currentIndex: tabBar.currentIndex

        // in the same "qml" folder
        DisplayPage {}
        VncPage {}
    }
}
