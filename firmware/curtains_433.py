import common
from machine import Pin
from rfsocket import RFSocket

CLIENT_ID = 'ALL_CURTAINS'
TOPIC_PREFIX = "%s/set" % CLIENT_ID
SUBTOPIC = [b"ALL_CURTAINS/set/#" % TOPIC_PREFIX, b"RFPOWER/set/#"]

relay_up = Pin(16, Pin.OUT)  # D0
relay_down = Pin(4, Pin.OUT) # D2

p = Pin(0, Pin.OUT)
s = RFSocket(p, remote_id=41203711, chann=RFSocket.NEXA)

def set_channel_state(channel, state):
    if state:
        s.on(channel)
    else:
        s.off(channel)
    common.mqtt.publish(PUBTOPIC+b"/%s" % channel, str(state))


def set_pin(pin, state):
    PUBTOPIC = b"%s/state/pin_%s" % (CLIENT_ID, str(pin))
    pin(state)
    if common.mqtt is not None:
        common.mqtt.publish(PUBTOPIC, str(pin()))

def move_curtains(direction, _time):
    if direction == 'up':
        relay = relay_up
    elif direction == 'down':
        relay = relay_down
    else:
        common.log("Got topic as %s" % str(topic))
        return

    import time
    common.log("Moving curtains %s for %d sec" % (topic, _time))

    set_pin(relay, False)
    for i in range(0, 10):
        time.sleep_ms(_time*100)
    set_pin(relay, True)

def sub_cb(topic, msg):
    stopic = topic.decode('ascii').split('/')
    if len(stopic) != 3:
        print(topic)
        common.log(topic)
        return

    if stopic[0] == 'ALL_CURTAINS':
        try:
            _time = int(msg.decode())
            _time = min(_time, 20)
        except Exception as e:
            common.log(e)
            return
        move_curtains(stopic[2], _time)
    elif stopic[0] == 'RFPOWER':
        channel = int(stopic[2])
        print(stopic[2], channel)
        if msg in (b'0', b'1'):
            set_channel_state(channel, int(msg))
        else:
            common.log(msg.decode('ascii'))

def setup():
    set_pin(relay_down, True)
    set_pin(relay_up, True)

def main():
    setup()
    common.loop(CLIENT_ID, setup_fn=None, loop_fn=[], callback=sub_cb, subtopic=SUBTOPIC)

main()
