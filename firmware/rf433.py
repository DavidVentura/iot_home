import common
import time
import dht
from machine import Pin
from rfsocket import RFSocket

CLIENT_ID = 'RFPOWER'
SUBTOPIC = b"%s/set/#" % CLIENT_ID
PUBTOPIC = b"%s/state" % CLIENT_ID
TEMPTOPIC = b"TEMP/%s" % CLIENT_ID
HUMTOPIC = b"HUM/%s" % CLIENT_ID

p = Pin(0, Pin.OUT)
s = RFSocket(p, remote_id=41203711, chann=RFSocket.NEXA)

def set_channel_state(channel, state):
    if state:
        s.on(channel)
    else:
        s.off(channel)
    common.mqtt.publish(PUBTOPIC+b"/%s" % channel, str(state))

def sub_cb(topic, msg):
    print(topic)
    print(msg)
    stopic = topic.decode('ascii').split('/')
    if len(stopic) != 3:
        common.log(topic)
        return
    channel = int(stopic[2])
    print(stopic[2], channel)
    if msg in (b'0', b'1'):
        set_channel_state(channel, int(msg))
    else:
        common.log(msg.decode('ascii'))

def main():
    #led(1) # Turn off LED, it is inverted
    common.loop(CLIENT_ID, setup_fn=None, loop_fn=[], callback=sub_cb, subtopic=SUBTOPIC)

main()
