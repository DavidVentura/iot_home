import json
import paho.mqtt.client as mqtt

class Mqtt:
    def __init__(self, host, port, topics, cb_list):
        self.mqttc = mqtt.Client()
        self.mqttc.connect(host, port=port)
        for topic in topics:
            self.mqttc.subscribe(topic, qos=0)

        self.mqttc.on_message = self.on_message
        self.cb_list = cb_list

    def on_message(self, client, userdata, message):
        msg = message.payload.decode('ascii')
        try:
            j = json.loads(message.payload.decode('ascii'))
        except json.decoder.JSONDecodeError:
            return
        for cb in self.cb_list:
            cb(message.topic, j)
    
    def loop_forever(self):
        self.mqttc.loop_forever()
