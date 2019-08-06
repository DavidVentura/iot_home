#!/usr/bin/env python3
import socket
import datetime
import time
import paho.mqtt.publish as publish
import sys
import json

HOST = ''
PORT = 12000

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
kindle_lamp_topic = 'NIGHTLAMP/set'
kindle_bat_topic = 'KINDLE/battery/state'
kindle_perc_topic = 'KINDLE/percentage/state'
iot_host = 'iot.labs'

try:
    s.bind((HOST, PORT))
except socket.error as msg:
    print('Bind failed. Error Code : ' + str(msg[0]) + ' Message ' + msg[1], flush=True)
    exit(1)

mac_mapping = {'f4:60:e2:b4:68:c4': "phones/david", 
               'a4:50:46:5b:fd:e1': "phones/tati",
               'bc:f5:ac:fd:3a:52': "phones/old-tati",
               '18:21:95:82:c0:a1': "phones/old-david",
              }
# TODO add logserver
while 1:
    try:
        print("Waiting..")
        message, address = s.recvfrom(1024)
        print(message, address, flush=True)
        curr_hour = time.localtime().tm_hour
        split = message.decode('ascii').split('|')
        key = split[0]
        if key == 'screen' or key == 'wifi':
            value = split[1]
            if curr_hour >= 22 or curr_hour <= 4:
                mqtt_message = '1' if value == 'on' else '0'
                print(mqtt_message, flush=True)
                publish.single(kindle_lamp_topic, mqtt_message, hostname=iot_host)
            else:
                print("Not doing anything as it is <22hs and >4hs", flush=True)
        elif key == 'book_status':
            value = json.loads(split[1])
            curr = value['pageBounds']['range']['begin']
            end = value['contentMetadata']['endOfBookPosition']
            percentage = round(float(curr)/float(end)*100, 1)
            print('Book percentage', percentage)
            publish.single(kindle_perc_topic, str(percentage), hostname=iot_host)
        elif key == 'bat':
            value = split[1]
            print('Bat level: %s' % value, flush=True)
            publish.single(kindle_bat_topic, str(value), hostname=iot_host)
        elif key == 'wlan0':
            state = split[1]
            mac = split[2].lower()
            if mac in mac_mapping:
                who = mac_mapping[mac]
                state = '1' if state == 'AP-STA-CONNECTED' else '0'
                print('mac state', who, state)
                publish.single('%s/state' % who, state, hostname=iot_host, retain=True)
            else:
                print('Unknown mac addr', mac, state)
        elif key == 'hdmi':
            value = split[1]
            print(value)
            publish.single('HDMI/state', value, hostname=iot_host, retain=True)
        sys.stdout.flush()
    except Exception as e:
        print(e, flush=True)
s.close()
