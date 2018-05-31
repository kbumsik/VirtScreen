import QtQuick 2.10
import QtQuick.Controls 2.3
import QtQuick.Controls.Material 2.3
import QtQuick.Layouts 1.3

Dialog {
    title: "VNC Options"
    focus: true
    modal: true
    visible: true
    standardButtons: Dialog.Ok
    x: (window.width - width) / 2
    y: (window.width - height) / 2 
    width: popupWidth
    height: 300

    Component.onCompleted: {
        var request = new XMLHttpRequest();
        request.open('GET', 'data.json');
        request.onreadystatechange = function(event) {
            if (request.readyState == XMLHttpRequest.DONE) {
                var data = JSON.parse(request.responseText).x11vncOptions;
                // merge data and settings
                for (var key in data) {
                    Object.assign(data[key], settings.x11vncOptions[key]);
                }
                var repeater = vncOptionsRepeater;
                repeater.model = Object.keys(data).map(function(k){return data[k]});
            }
        };
        request.send();
    }

    ColumnLayout {
        anchors.fill: parent

        Repeater {
            id: vncOptionsRepeater
            RowLayout {
                enabled: modelData.available
                Label {
                    Layout.fillWidth: true
                    text: modelData.description + ' (' + modelData.value + ')' 
                }
                Switch {
                    checked: modelData.available ? modelData.enabled : false
                    onCheckedChanged: {
                        settings.x11vncOptions[modelData.value].enabled = checked;
                    }
                }
            }
        }

        RowLayout {
            // Empty layout
            Layout.fillHeight: true
        }
    }
    onAccepted: {}
    onRejected: {}
}
