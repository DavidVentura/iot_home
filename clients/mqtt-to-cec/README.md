# MQTT to HDMI-CEC
This simple project parses data it receives from MQTT and emits CEC commands (by communicating with `cec-client`).

This is particularly useful on a KODI system like CoreELEC.

You can build it by running `GOARCH=arm go build`
