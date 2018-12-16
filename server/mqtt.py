import json
import paho.mqtt.client as mqtt

class Mqtt:
    def __init__(self, host, port, topics, cb_list, _json=True):
        self.mqttc = mqtt.Client()
        self.mqttc.connect(host, port=port)
        for topic in topics:
            self.mqttc.subscribe(topic, qos=0)

        self.mqttc.on_message = self.on_message
        self.cb_list = cb_list
        self.json = _json

    def on_message(self, client, userdata, message):
        msg = message.payload.decode('ascii')
        try:
            if self.json:
                j = json.loads(message.payload.decode('ascii'))
            else:
                j = message.payload.decode('ascii')
        except json.decoder.JSONDecodeError:
            print("Failed to decode JSON")
            return
        for cb in self.cb_list:
            cb(message.topic, j)
    
    def loop_forever(self):
        self.mqttc.loop_forever()
