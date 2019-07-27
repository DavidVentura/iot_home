#!/usr/bin/env python3
import configparser
import requests
import time
import datetime

from mqtt import Mqtt

GRAFANA_URL = "http://db.labs:8086/write?db=sensordata"


def setup():
    host = 'iot'
    port = 1883
    topics = ["TEMP/TEMPSENSOR", "HUM/TEMPSENSOR", "HUM/#", "TEMP/#", "NIGHTLAMP2/state", "KINDLE/battery/state", "KINDLE/percentage/state", "phones/#"]
    # CONFIG
    return Mqtt(host, port, topics, [to_influx], _json=False)

def main():
    mqttc = setup()
    print('setupok')
    try:
        mqttc.loop_forever()
    except KeyboardInterrupt:
        print("Interrupt detected, exiting")
        pass

def to_influx(topic, value):
    print(datetime.datetime.now(), topic, value)

    _type = topic.split('/')[0]
    sensor = topic.split('/')[1]
    _data = '%s,sensor="%s" value=%f' % (_type, sensor, float(value))
    try:
        response = requests.post(GRAFANA_URL, data=_data, timeout=2)
        if not response.ok:
            print(_data)
            print(response)
            print(response.text)
    except Exception as e:
        print(e)

    
if __name__ == '__main__':
    main()
