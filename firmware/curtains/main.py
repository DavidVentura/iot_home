import common
import time
from machine import Pin

CLIENT_ID = common.get_client_id()
SUBTOPIC = b"%s/set/#" % CLIENT_ID

relay_up = Pin(16, Pin.OUT)  # D0
relay_down = Pin(4, Pin.OUT) # D2

p = Pin(0, Pin.OUT)

def set_pin(pin, state):
    PUBTOPIC = b"%s/state/pin_%s" % (CLIENT_ID, str(pin))
    pin(state)
    common.publish(PUBTOPIC, str(pin()))

def move_curtains(direction, _time):
    if direction == 'up':
        relay = relay_up
    elif direction == 'down':
        relay = relay_down
    else:
        common.log("Got topic as %s" % str(topic))
        return

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

    try:
        _time = int(msg.decode())
        _time = min(_time, 20)
    except Exception as e:
        common.log(e)
        return
    move_curtains(stopic[2], _time)

def setup():
    set_pin(relay_down, True)
    set_pin(relay_up, True)

def main():
    setup()
    common.loop(setup_fn=None, loop_fn=[], callback=sub_cb, subtopic=[SUBTOPIC])

main()
