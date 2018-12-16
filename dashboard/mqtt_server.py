#!/usr/bin/env python3.6
import logging
import json
import paho.mqtt.client as mqtt

topics = ['NIGHTLAMP/state', 'TEMP/#', 'HUM/#', 'ALL_CURTAINS/#', 'HOME/KODI_STATUS', 'LIGHTS/#', 'RFPOWER/#']

def on_msg_wrapper(q):
    def on_message(client, userdata, message):
        msg = message.payload.decode('ascii')
        topic = message.topic
        print('> %s: %s' % (topic, msg), flush=True)
        q.put((topic, msg))
    return on_message

def serve(mqtt_q, ws_q):
    mqttc = mqtt.Client()
    print('connecting', flush=True)
    mqttc.connect('iot.labs')
    for topic in topics:
        print('subscribing to %s' % topic, flush=True)
        mqttc.subscribe(topic, qos=0)
    mqttc.on_message = on_msg_wrapper(mqtt_q)
    mqttc.loop_start()
    while True:
        data = ws_q.get()
        print('mqtt got %s' % data, flush=True)
        for topic, value in data.items():
            mqttc.publish(topic, value, retain=False)
    print('finished serving mqtt', flush=True)
