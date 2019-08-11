#!/usr/bin/env python3
import configparser
import requests
import time
import datetime

from mqtt import Mqtt

GRAFANA_URL = "http://db.labs:8086/write?db=sensordata"
custom_parsing = { 'printer': printer_parsing }

def setup():
    host = 'iot'
    port = 1883
    topics = ["TEMP/TEMPSENSOR", "HUM/TEMPSENSOR", "HUM/#", "TEMP/#", "NIGHTLAMP2/state", "KINDLE/battery/state", "KINDLE/percentage/state", "phones/#", "printer/#"]
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
    if _type in custom_parsing:
        custom_parsing[_type](topic, value)
    else:
        default_parsing(topic, value)

def post_to_grafana(data):
        try:
            response = requests.post(GRAFANA_URL, data=_data, timeout=2)
            if not response.ok:
                print(_data)
                print(response)
                print(response.text)
        except Exception as e:
            print(e)


def printer_parsing(topic, value):
    _type = topic.split('/')[0]
    if topic == "printer/JOB_STATUS":
        _data = 'printer_job_status percentage=%f' % (float(value))
        post_to_grafana(_data)
    elif topic == "printer/TEMP":
        nozzle, bed = value.split(',')
        for sensor, current, target in [['nozzle']+nozzle.split('/'), ['bed']+bed.split('/')]
            _data = 'printer_temp,sensor="%s" current=%f,target=%f' % (sensor, float(current), float(target))
            post_to_grafana(_data)


def default_parsing(topic, value):
    _type = topic.split('/')[0]
    sensor = topic.split('/')[1]
    _data = '%s,sensor="%s" value=%f' % (_type, sensor, float(value))
    post_to_grafana(_data)
    
if __name__ == '__main__':
    main()
