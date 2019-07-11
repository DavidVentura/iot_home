import common
import time
import dht
from machine import Pin

CLIENT_ID = 'NIGHTLAMP'
SUBTOPIC = b"%s/set" % CLIENT_ID
PUBTOPIC = b"%s/state" % CLIENT_ID
TEMPTOPIC = b"TEMP/%s" % CLIENT_ID
HUMTOPIC = b"HUM/%s" % CLIENT_ID

button = Pin(0, Pin.IN)
led = Pin(13, Pin.OUT)
relay = Pin(12, Pin.OUT)
dht = dht.DHT22(Pin(14))

def set_pin(pin, state):
    common.log('Setting pin to %s' % state)
    pin(state)
    common.publish(PUBTOPIC, str(pin()))

def sub_cb(topic, msg):
    common.log(topic)
    common.log(msg)
    if msg == b'1':
        set_pin(relay, True)
    elif msg == b'0':
        set_pin(relay, False)
    else:
        set_pin(relay, not relay())

@common.debounce(300000)
def read_dht():
    try:
        dht.measure()
    except Exception as e:
        common.log('Failed to get DHT measurements: %s' % e)
        return
    common.publish(TEMPTOPIC, "%.2f" % dht.temperature())
    common.publish(HUMTOPIC, "%.2f" % dht.humidity())

@common.debounce(250)
def handle_button(pin):
    common.log('Button was pressed')
    set_pin(relay, not relay())

def setup():
    button.irq(handler=handle_button, trigger=Pin.IRQ_RISING),
    led(1) # Turn off LED, it is inverted

def main():
    common.loop(setup_fn=setup, loop_fn=[read_dht], callback=sub_cb, subtopic=[SUBTOPIC])

main()
