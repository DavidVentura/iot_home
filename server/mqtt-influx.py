#!/usr/bin/env python3
import configparser
import requests
import time
import datetime

from mqtt import Mqtt

GRAFANA_URL = "http://grafana.labs:8086/write?db=sensordata"


def setup():
    host = 'iot'
    port = 1883
    topics = ["TEMP/TEMPSENSOR", "HUM/TEMPSENSOR", "HUM/NIGHTLAMP2", "TEMP/NIGHTLAMP2", "NIGHTLAMP2/state"]
    # CONFIG
    return Mqtt(host, port, topics, [to_influx])

def main():
    mqttc = setup()
    try:
        mqttc.loop_forever()
    except KeyboardInterrupt:
        print("Interrupt detected, exiting")
        pass

def to_influx(topic, value):
    tstamp = int(time.mktime(datetime.datetime.now().timetuple()))
    influx_tstamp = tstamp * 1000000000

    _type = topic.split('/')[0]
    sensor = topic.split('/')[1]
    _data = '%s sensor="%s",value=%f' % (_type, sensor, float(value))
    response = requests.post(GRAFANA_URL, data=_data)
    if not response.ok:
        print(_data)
        print(response)
        print(response.text)

    
if __name__ == '__main__':
    main()
