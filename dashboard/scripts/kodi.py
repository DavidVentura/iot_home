#!/usr/bin/python3
import json
import paho.mqtt.client as mqtt
import requests
import time
from threading import Thread

KODI_URL = 'http://libreelec.labs:8080/jsonrpc'

def cast(port):
    headers = {"content-type": "application/json"}
    payload = {"jsonrpc": "2.0",
               "method": "Player.Open",
               "params": {
                   "item": {
                       "file": "tcp://twitch.labs:%s" % port}
                },
               "id": 1}
    url = 'http://libreelec.labs:8080/jsonrpc'

    r = requests.post(url, headers=headers, data=json.dumps(payload))

def get_playing():
    r = requests.get("http://twitch.labs/twitch/stream_list")
    return r.json()

def cast_whatever():
    playing = get_playing()
    if len(playing) == 0:
        return
    to_cast = playing[0]
    print(to_cast)
    cast(to_cast['port'])

def stop_kodi():
    r = requests.get('http://libreelec.labs:8080/jsonrpc?Player.GetActivePlayers', json=[{"jsonrpc":"2.0","method":"Player.GetActivePlayers","params":{},"id":15}])
    pid = r.json()[0]["result"][0]["playerid"]
    r = requests.post('%s?Player.Stop' % KODI_URL, json=[{"jsonrpc":"2.0","method":"Player.Stop","params":{"playerid": pid},"id":1}])
    print(r.json())

def get_kodi_playing():
    headers = {"content-type": "application/json"}
    payload = {"jsonrpc": "2.0", "id": 1, "method": "Playlist.GetPlaylists"}
    url = 'http://libreelec.labs:8080/jsonrpc'
    req = requests.post(url, headers=headers, data=json.dumps(payload))
    playlists = json.loads(req.text)
    valid = False
    if 'result' in playlists:
        for _type in playlists['result']:
            if _type['type'] == 'video':
                valid = True
    if not valid:
        return ''

    payload = {"jsonrpc": "2.0", "method": "Player.GetItem",
               "params": {
                   "properties": ["file", "streamdetails"],
                   "playerid": 1},
               "id": "VideoGetItem"}
    req = requests.post(url, headers=headers, data=json.dumps(payload))
    result = json.loads(req.text)
    ret = ''
    try:
        ret = result["result"]["item"]["file"]
    except:
        ret = ''
    return ret

def on_message(client, userdata, message):
    msg = message.payload.decode('ascii')
    topic = message.topic
    print(topic, msg)
    if 'CAST' in topic:
        cast_whatever()
        update_kodi_status(client)
    elif 'STOP' in topic:
        print('stopping kodi')
        stop_kodi()
        update_kodi_status(client)

def update_kodi_status(mqttc):
    print('updating kodi')
    mqttc.publish('HOME/KODI_STATUS', get_kodi_playing())
    print('updated kodi')
    
def main():
    mqttc = mqtt.Client()
    mqttc.connect('iot.labs')
    time.sleep(0.5)
    mqttc.subscribe([('HOME/KODI/CAST_WHATEVER', 0), ('HOME/KODI/STOP', 0)])
    mqttc.on_message = on_message
    mqttc.loop_start()
    while True:
        print('sleeping')
        for i in range(0, 20):
            time.sleep(1)

        update_kodi_status(mqttc)
        #t = Thread(target=update_kodi_status, args=(mqttc,))
        #t.daemon = True
        #t.start()
 
main()
