import common
import dht
from machine import Pin

CLIENT_ID = 'TEMPSENSOR'
TEMPTOPIC = b"TEMP/%s" % CLIENT_ID
HUMTOPIC = b"HUM/%s" % CLIENT_ID

led = Pin(13, Pin.OUT)
dht = dht.DHT22(Pin(14))

@common.debounce(60000)
def read_dht():
    dht.measure()
    common.mqtt.publish(TEMPTOPIC, "%.2f" % dht.temperature())
    common.mqtt.publish(HUMTOPIC, "%.2f" % dht.humidity())

def main():
    setup_fns = [ lambda: led(1) # Turn off LED, it is inverted
                ]
    common.loop(CLIENT_ID, setup_fn=setup_fns, loop_fn=[read_dht], callback=sub_cb, subtopic=SUBTOPIC)

main()
