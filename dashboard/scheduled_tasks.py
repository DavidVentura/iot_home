#!/usr/bin/env python3
import datetime
import paho.mqtt.publish as publish

import requests
import sched
import time
import math

COORDINATES = {'lat': 52.3415, 'lon': 4.9549}
HOUR = 3600
scheduler = sched.scheduler(time.time, time.sleep)

def distance(p1, p2):
    x1, x2 = p1['lat'], p2['lat']
    y1, y2 = p1['lon'], p2['lon']
    return math.sqrt((x1-x2)**2 + (y1-y2)**2)

def closest_station(stations):
    closest = None
    min_distance = 9999
    for station in stations:
        d = distance(COORDINATES, station)
        if d < min_distance:
            closest = station
            min_distance = d
    return closest

def buien_data():
    r = requests.get('https://api.buienradar.nl/data/public/2.0/jsonfeed', timeout=5)
    if not r.ok:
        print(r.text)
        return
    j = r.json()
    ss = datetime.datetime.strptime(j['actual']['sunset'], "%Y-%m-%dT%H:%M:%S")
    station = closest_station(j['actual']['stationmeasurements'])
    # ssinflux = ss.timestamp()*1000000000
    return {'sunset': ss, 'station': station}

def every(interval):
    def cdecorator(func):
        def wrapper(*args, **kwargs):
            func(*args, **kwargs)
            scheduler.enter(interval, 1, every(interval)(func), argument=args, kwargs=kwargs)
            print("Scheduling %s in %s seconds with args: %s and kwargs %s" % (func.__name__, interval, args, kwargs))
        return wrapper
    return cdecorator

@every(24*HOUR)
def schedule_sunset():
    data = buien_data()
    # print(data)
    sunset_ts = data['sunset'].timestamp()
    args = ('RFPOWER/set/2', '1')
    kwargs = {'hostname': 'iot', 'retain': True}
    scheduler.enterabs(sunset_ts, 1, publish.single, argument=args, kwargs=kwargs)

# initial scheduling
scheduler.enter(2, 1, schedule_sunset)

# TODO curtains? buienradar?
while True:
    scheduler.run(blocking=False)
    time.sleep(2)
