import QtQuick 2.10
import QtQuick.Controls 2.3
import QtQuick.Controls.Material 2.3
import QtQuick.Layouts 1.3

Dialog {
    id: preferenceDialog
    title: "Preference"
    focus: true
    modal: true
    visible: true
    standardButtons: Dialog.Ok
    x: (window.width - width) / 2
    y: (window.width - height) / 2 
    width: popupWidth
    ColumnLayout {
        anchors.fill: parent
        RowLayout {
            anchors.left: parent.left
            anchors.right: parent.right
            Label { id: themeColorLabel; text: "Theme Color"; }
            ComboBox {
                id: themeColorComboBox
                anchors.left: themeColorLabel.right
                anchors.right: parent.right
                anchors.leftMargin: 50
                Material.background: currentIndex
                Material.foreground: "white"
                textRole: "name"
                model: [{"value": Material.Red, "name": "Red"}, {"value": Material.Pink, "name": "Pink"},
                        {"value": Material.Purple, "name": "Purple"},{"value": Material.DeepPurple, "name": "DeepPurple"},
                        {"value": Material.Indigo, "name": "Indigo"}, {"value": Material.Blue, "name": "Blue"},
                        {"value": Material.LightBlue, "name": "LightBlue"}, {"value": Material.Cyan, "name": "Cyan"},
                        {"value": Material.Teal, "name": "Teal"}, {"value": Material.Green, "name": "Green"},
                        {"value": Material.LightGreen, "name": "LightGreen"}, {"value": Material.Lime, "name": "Lime"},
                        {"value": Material.Yellow, "name": "Yellow"}, {"value": Material.Amber, "name": "Amber"},
                        {"value": Material.Orange, "name": "Orange"}, {"value": Material.DeepOrange, "name": "DeepOrange"},
                        {"value": Material.Brown, "name": "Brown"}, {"value": Material.Grey, "name": "Grey"},
                        {"value": Material.BlueGrey, "name": "BlueGrey"}]
                currentIndex: settings.theme_color
                onActivated: function(index) {
                    window.theme_color = index;
                    settings.theme_color = index;
                } 
                delegate: ItemDelegate {
                    width: parent.width
                    text: modelData.name + (themeColorComboBox.currentIndex === index ? " (Current)" : "")
                    Material.foreground: "white"
                    background: Rectangle {
                        color: Material.color(modelData.value)
                    }
                }
            }
        }
    }
    onAccepted: {}
    onRejected: {}
}
