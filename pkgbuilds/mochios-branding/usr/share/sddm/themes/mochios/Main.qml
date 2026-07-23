import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    width: Screen.width
    height: Screen.height
    color: "#231937"

    Rectangle {
        anchors.centerIn: parent
        width: 400
        height: 400
        color: "#2f1f4f"
        radius: 20

        ColumnLayout {
            anchors.centerIn: parent
            spacing: 20

            Text {
                text: "mochios"
                color: "#e6dcf0"
                font.pixelSize: 48
                font.bold: true
                anchors.horizontalCenter: parent.horizontalCenter
            }

            TextField {
                id: username
                placeholderText: "username"
                color: "#e6dcf0"
                background: Rectangle {
                    color: "#1a0f30"
                    radius: 8
                }
                Layout.fillWidth: true
                Keys.onReturnPressed: password.forceActiveFocus()
            }

            TextField {
                id: password
                placeholderText: "password"
                echoMode: TextInput.Password
                color: "#e6dcf0"
                background: Rectangle {
                    color: "#1a0f30"
                    radius: 8
                }
                Layout.fillWidth: true
                Keys.onReturnPressed: sddm.login(username.text, password.text)
            }

            Button {
                text: "log in"
                onClicked: sddm.login(username.text, password.text)
                Layout.fillWidth: true
                background: Rectangle {
                    color: "#9664c8"
                    radius: 8
                }
                contentItem: Text {
                    text: "log in"
                    color: "#ffffff"
                    horizontalAlignment: Text.AlignHCenter
                }
            }
        }
    }
}
