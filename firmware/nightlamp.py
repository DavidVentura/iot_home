import common
import time
from machine import Pin

CLIENT_ID = 'NIGHTLAMP'
SUBTOPIC = b"%s/set" % CLIENT_ID
PUBTOPIC = b"%s/state" % CLIENT_ID

button = Pin(0, Pin.IN)
led = Pin(13, Pin.OUT)
relay = Pin(12, Pin.OUT)

def set_pin(pin, state):
    pin(state)
    common.mqtt.publish(PUBTOPIC, str(pin()))

def sub_cb(topic, msg):
    if msg == b'1':
        set_pin(relay, True)
    elif msg == b'0':
        set_pin(relay, False)
    else:
        set_pin(relay, not relay())

@common.debounce(250)
def handle_button(pin):
    set_pin(relay, not relay())

def setup():
    button.irq(handler=handle_button, trigger=Pin.IRQ_RISING),
    led(1) # Turn off LED, it is inverted
def main():
    common.loop(CLIENT_ID, setup_fn=setup, loop_fn=[], callback=sub_cb, subtopic=SUBTOPIC)

main()
