import common
from machine import Pin

CLIENT_ID = 'ALL_CURTAINS'
TOPIC_PREFIX = "%s/set" % CLIENT_ID
SUBTOPIC = b"%s/#" % TOPIC_PREFIX

relay_up = Pin(16, Pin.OUT)  # D0
relay_down = Pin(4, Pin.OUT) # D2

def set_pin(pin, state):
    PUBTOPIC = b"%s/state/pin_%s" % (CLIENT_ID, str(pin))
    pin(state)
    if common.mqtt is not None:
        common.mqtt.publish(PUBTOPIC, str(pin()))

def sub_cb(topic, msg):
    topic = topic.decode().replace(TOPIC_PREFIX + '/', '').lower()
    if topic == 'up':
        relay = relay_up
    elif topic == 'down':
        relay = relay_down
    else:
        common.log("Got topic as %s" % str(topic))
        return

    import time
    try:
        _time = int(msg.decode())
        _time = min(_time, 20)
    except Exception as e:
        common.log(e)
        return
    common.log("Moving curtains %s for %d sec" % (topic, _time))

    set_pin(relay, False)
    for i in range(0, 10):
        time.sleep_ms(_time*100)
    set_pin(relay, True)

def setup():
    set_pin(relay_down, True)
    set_pin(relay_up, True)

def main():
    setup()
    common.loop(CLIENT_ID, setup_fn=None, loop_fn=[], callback=sub_cb, subtopic=SUBTOPIC)

main()
