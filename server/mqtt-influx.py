#!/usr/bin/env python3
import datetime
import json

import requests

from mqtt import Mqtt

GRAFANA_URL = "http://db.labs:8086/write?db=sensordata"

def setup():
    host = 'iot'
    port = 1883
    topics = ["TEMP/TEMPSENSOR", "HUM/TEMPSENSOR", "HUM/#", "TEMP/#", "NIGHTLAMP2/state", "KINDLE/#", "phones/#", "printer/#", "LUX/state", "DESK/state"]
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
    custom_parsing = { 'printer': printer_parsing, 'KINDLE': kindle_parsing }
    print(datetime.datetime.now(), topic, value)
    _type = topic.split('/')[0]
    if _type in custom_parsing:
        custom_parsing[_type](topic, value)
    else:
        default_parsing(topic, value)

def post_to_grafana(data):
        try:
            response = requests.post(GRAFANA_URL, data=data, timeout=3)
            if not response.ok:
                print(data)
                print(response)
                print(response.text)
        except Exception as e:
            print(e)


def kindle_parsing(topic, value):
    if topic != "KINDLE/BOOK":
        return default_parsing(topic, value)

    try:
        data = json.loads(value)
    except Exception as e:
        print(e)
        return
    page_position = int(data['pageBounds']['range']['begin'])
    book_title = data['contentItem']['title']
    book_length = data['contentItem']['bookLength']
    book_percentage = (page_position / book_length)*100
    _data = 'KINDLE,sensor=BOOK percentage=%f,book="%s"' % (float(book_percentage), book_title)
    print(_data)
    post_to_grafana(_data)


def printer_parsing(topic, value):
    if topic == "printer/JOB_STATUS":
        _data = 'printer_job_status percentage=%f' % (float(value))
        post_to_grafana(_data)
    elif topic == "printer/TEMP":
        nozzle, bed = value.split(',')
        for sensor, current, target in [['nozzle']+nozzle.split('/'), ['bed']+bed.split('/')]:
            _data = 'printer_temp,sensor=%s current=%f,target=%f' % (sensor, float(current), float(target))
            post_to_grafana(_data)


def default_parsing(topic, value):
    _type = topic.split('/')[0]
    sensor = topic.split('/')[1]
    _data = '%s,sensor=%s value=%f' % (_type, sensor, float(value))
    post_to_grafana(_data)
    
if __name__ == '__main__':
    main()
