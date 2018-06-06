import QtQuick 2.10
import QtQuick.Controls 2.3
import QtQuick.Controls.Material 2.3
import QtQuick.Layouts 1.3

Dialog {
    title: "Display Options"
    focus: true
    modal: true
    visible: true
    standardButtons: Dialog.Ok
    x: (window.width - width) / 2
    y: (window.width - height) / 2 
    width: popupWidth
    height: 250

    ColumnLayout {
        anchors.fill: parent

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
                currentIndex: {
                    if (settings.virt.device) {
                        for (var i = 0; i < model.length; i++) {
                            if (model[i].name == settings.virt.device) {
                                return i;
                            }
                        }
                    }
                    settings.virt.device = '';
                    return -1;
                }  
                onActivated: function(index) {
                    settings.virt.device = model[index].name;
                } 
                delegate: ItemDelegate {
                    width: deviceComboBox.width
                    text: modelData.name
                    font.weight: deviceComboBox.currentIndex === index ? Font.Bold : Font.Normal
                    enabled: modelData.connected ? false : true
                }
            }
        }

        Text {
            Layout.fillWidth: true
            font { pixelSize: 14 }
            wrapMode: Text.WordWrap
            text: "<b>Warning</b>: Edit only if 'VIRTUAL1' is not available. " +
                  "If so, please note that the virtual screen may be " +
                  "unstable/unavailable depending on a graphic " +
                  "card and its driver."
        }
        
        RowLayout {
            // Empty layout
            Layout.fillHeight: true
        }
    }
    onAccepted: {}
    onRejected: {}
}
