import QtQuick 2.10
import QtQuick.Controls 2.3
import QtQuick.Layouts 1.3

import VirtScreen.Backend 1.0

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