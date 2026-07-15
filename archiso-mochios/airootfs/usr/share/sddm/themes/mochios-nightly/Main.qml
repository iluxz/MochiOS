import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    width: 1920
    height: 1080
    color: "#0d0719"

    Canvas {
        anchors.fill: parent
        onPaint: {
            var ctx = getContext("2d")
            if (!ctx) return

            var stars = [
                [0.08, 0.05, 1.5, 0.9], [0.15, 0.12, 1.0, 0.6],
                [0.22, 0.03, 2.0, 1.0], [0.30, 0.18, 1.2, 0.7],
                [0.05, 0.25, 1.0, 0.5], [0.42, 0.08, 1.8, 0.8],
                [0.55, 0.15, 1.0, 0.4], [0.65, 0.05, 1.3, 0.7],
                [0.35, 0.22, 0.8, 0.5], [0.48, 0.28, 1.5, 0.9],
                [0.60, 0.20, 1.0, 0.6], [0.18, 0.32, 1.2, 0.8],
                [0.25, 0.08, 0.7, 0.4], [0.72, 0.12, 1.6, 0.7],
                [0.10, 0.18, 1.1, 0.5], [0.38, 0.15, 0.9, 0.6],
                [0.50, 0.10, 1.4, 0.8], [0.68, 0.25, 1.0, 0.5],
                [0.20, 0.28, 0.8, 0.7], [0.45, 0.05, 1.2, 0.9]
            ]

            for (var i = 0; i < stars.length; i++) {
                var s = stars[i]
                ctx.globalAlpha = s[3]
                ctx.fillStyle = "#ffffff"
                ctx.beginPath()
                ctx.arc(s[0] * width, s[1] * height, s[2], 0, Math.PI * 2)
                ctx.fill()
            }
            ctx.globalAlpha = 1.0
        }
    }

    Canvas {
        anchors.fill: parent
        onPaint: {
            var ctx = getContext("2d")
            if (!ctx) return

            var mx = width * 0.78
            var my = height * 0.15
            var gradient = ctx.createRadialGradient(mx, my, 10, mx, my, 200)
            gradient.addColorStop(0, "rgba(232, 216, 248, 0.12)")
            gradient.addColorStop(1, "rgba(232, 216, 248, 0)")
            ctx.fillStyle = gradient
            ctx.beginPath()
            ctx.arc(mx, my, 200, 0, Math.PI * 2)
            ctx.fill()
        }
    }

    Canvas {
        anchors.fill: parent
        onPaint: {
            var ctx = getContext("2d")
            if (!ctx) return

            var mx = width * 0.78
            var my = height * 0.15

            ctx.beginPath()
            ctx.arc(mx, my, 70, 0, Math.PI * 2)
            ctx.fillStyle = "#f0e8ff"
            ctx.fill()

            ctx.save()
            ctx.globalCompositeOperation = "destination-out"
            ctx.beginPath()
            ctx.arc(mx + 22, my - 16, 55, 0, Math.PI * 2)
            ctx.fill()
            ctx.restore()
        }
    }

    Rectangle {
        anchors.centerIn: parent
        width: 420
        height: 420
        color: "#1a0f30"
        radius: 24
        border.color: "#3a2a5a"
        border.width: 1

        ColumnLayout {
            anchors.centerIn: parent
            spacing: 20

            Text {
                text: "mochios"
                color: "#e6dcf0"
                font.pixelSize: 52
                font.bold: true
                Layout.alignment: Qt.AlignHCenter
            }

            Text {
                text: "NIGHTLY"
                color: "#9664c8"
                font.pixelSize: 18
                font.letterSpacing: 8
                Layout.alignment: Qt.AlignHCenter
                opacity: 0.7
            }

            Item { width: 1; height: 10 }

            TextField {
                id: username
                placeholderText: "username"
                Layout.preferredWidth: 280
                Layout.alignment: Qt.AlignHCenter
                background: Rectangle { color: "#0d0719"; radius: 8 }
                color: "#e6dcf0"
                placeholderTextColor: "#6a5a8a"
                Keys.onReturnPressed: password.forceActiveFocus()
            }

            TextField {
                id: password
                placeholderText: "password"
                echoMode: TextInput.Password
                Layout.preferredWidth: 280
                Layout.alignment: Qt.AlignHCenter
                background: Rectangle { color: "#0d0719"; radius: 8 }
                color: "#e6dcf0"
                placeholderTextColor: "#6a5a8a"
                Keys.onReturnPressed: sddm.login(username.text, password.text)
            }

            Button {
                text: "log in"
                Layout.preferredWidth: 280
                Layout.alignment: Qt.AlignHCenter
                onClicked: sddm.login(username.text, password.text)
                background: Rectangle { color: "#9664c8"; radius: 8 }
                contentItem: Text { text: "log in"; color: "#ffffff"; font.bold: true; horizontalAlignment: Text.AlignHCenter }
            }
        }
    }

    Text {
        text: "NIGHTLY BUILD"
        color: "#9664c8"
        font.pixelSize: 13
        font.bold: true
        letterSpacing: 4
        opacity: 0.3
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.margins: 24
    }
}
