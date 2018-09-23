# IOT Home

The idea of this repo is to create a framework of some sort to easily add new sensors to my IOT network.
You can see more info [here](https://blog.davidventura.com.ar/iot-house-with-sonoff-and-micropython-part-1.html), but the gist of it is:

* Written in MicroPython (sensors) and Python3 (services)
* Clients subscribe/publish to MQTT 
* A daemon on a real box converts this to whatever protocol necessary
* You shouldn't need to write more than ~40 lines of code for your sensor
* OTA updates included
* Remote logging (simple messages sent via UDP)
* The program flow is inspired by Arduino; setup followed by loop()
    * You have to set up your IRQ handlers during setup


# Pushing an OTA update

Simply run `./server/OTA_sender.py --target NIGHTLAMP firmware/main.py` to push `main.py` to the sensor `NIGHTLAMP` and reboot it.

# Sensor data to grafana

This consists of a simple sensor ([temp.py](firmware/temp.py)) that reads from a DHT22 every 60s and publishes temperature and humidity data.
Then the [mqtt-influx](server/mqtt-influx.py) service is in charge of POSTing that data to InfluxDB.

# Example sensor

The code for a sensor that:
* Toggles a GPIO on button press
* Sets the GPIO state on an incoming MQTT message
* Publishes the button status (on change) to MQTT

is as trivial as:

```python
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
    common.log('Someone pressed the button!')

def main():
    setup_fns = [ lambda: button.irq(handler=handle_button, trigger=Pin.IRQ_RISING),
                  lambda: led(1) # Turn off LED, it is inverted
                ]
    common.loop(CLIENT_ID, setup_fn=setup_fns, loop_fn=[], callback=sub_cb, subtopic=SUBTOPIC)

main()
```


(see [nightlamp.py](firmware/nightlamp.py))
