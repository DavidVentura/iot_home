#!/usr/bin/env python3
import datetime
import json
import os

from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

from mqtt import Mqtt

token = os.environ['INFLUX_TOKEN']
org = "org"
bucket = "sensordata/autogen"
client = InfluxDBClient(url="http://db.labs:8086", token=token)
write_api = client.write_api(write_options=SYNCHRONOUS)

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

def post_to_influxv2(data):
        try:
            write_api.write(bucket, org, data)
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
    _data = 'KINDLE,sensor=BOOK,book=%s percentage=%f' % (book_title.replace(' ', '_'), int(book_percentage))
    post_to_influxv2(_data)


def printer_parsing(topic, value):
    if topic == "printer/JOB_STATUS":
        _data = 'printer_job_status percentage=%f' % (float(value))
        post_to_influxv2(_data)
    elif topic == "printer/TEMP":
        nozzle, bed = value.split(',')
        for sensor, current, target in [['nozzle']+nozzle.split('/'), ['bed']+bed.split('/')]:
            _data = 'printer_temp,sensor=%s current=%f,target=%f' % (sensor, float(current), float(target))
            post_to_influxv2(_data)


def default_parsing(topic, value):
    _type = topic.split('/')[0]
    sensor = topic.split('/')[1]
    _data = '%s,sensor=%s value=%f' % (_type, sensor, float(value))
    post_to_influxv2(_data)
    
if __name__ == '__main__':
    main()
