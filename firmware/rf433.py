import common
import time
import dht
from machine import Pin
from rfsocket import RFSocket

CLIENT_ID = 'RFPOWER'
HDMI_SUBTOPIC = b"HDMI/set/#"
HDMI_PUBTOPIC = b"HDMI/state"

LAMP_SUBTOPIC = b"%s/set/#" % CLIENT_ID
LAMP_PUBTOPIC = b"%s/state" % CLIENT_ID
HDMI_PIN = Pin(4, Pin.OUT)

p = Pin(0, Pin.OUT)
s = RFSocket(p, remote_id=41203711, chann=RFSocket.NEXA)

def set_channel_state(channel, state):
    if state:
        s.on(channel)
    else:
        s.off(channel)
    common.publish(LAMP_PUBTOPIC+b"/%s" % channel, str(state))

def set_pin(pin, state, pubtopic):
    common.log('Setting pin to %s, publishing to %s' % (state, pubtopic))
    pin(state)
    common.publish(pubtopic, str(pin()))

def sub_cb(topic, msg):
    stopic = topic.decode('ascii').split('/')
    common.log('Topic: %s' % topic.decode('ascii'))
    common.log('Msg: %s' % msg.decode('ascii'))
    if stopic[0] == CLIENT_ID:
        if len(stopic) != 3:
            common.log(topic)
            return
        channel = int(stopic[2])
        if msg in (b'0', b'1'):
            set_channel_state(channel, int(msg))
    if stopic[0] == 'HDMI':
        set_pin(HDMI_PIN, not HDMI_PIN(), HDMI_PUBTOPIC)

def main():
    #led(1) # Turn off LED, it is inverted
    common.loop(CLIENT_ID, setup_fn=None, loop_fn=[], callback=sub_cb, subtopic=[LAMP_SUBTOPIC, HDMI_SUBTOPIC])

main()
