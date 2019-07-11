# IOT Home

The idea of this repo is to create a framework of some sort to easily add new sensors to my IOT network.
You can see more info [here](https://blog.davidventura.com.ar/iot-house-with-sonoff-and-micropython.html), but the gist of it is:

* Written in MicroPython (sensors) and Python3 (services)
* Clients subscribe/publish to MQTT 
* A daemon on a real box converts this to whatever protocol necessary
* You shouldn't need to write more than ~40 lines of code for your sensor
* OTA updates included
* Remote logging (simple messages sent via UDP)
* The program flow is an event loop; setup followed by loop()
    * You have to set up your IRQ handlers during setup
* By providing a `HOSTNAME` file you can set your device's name. It will be used for DHCP and MQTT topics.


# Pushing an OTA update

Simply run `./server/OTA_sender.py --target NIGHTLAMP firmware/nightlamp/main.py --reboot` to push `main.py` to the sensor `NIGHTLAMP` and reboot it.

# Sensor data to grafana

This consists of a simple sensor ([main.py](firmware/nightlamp/main.py)) that reads from a DHT22 every 300s and publishes temperature and humidity data.
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
    common.publish(PUBTOPIC, str(pin()))

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
    setup_fns = [lambda: button.irq(handler=handle_button, trigger=Pin.IRQ_RISING),
                 lambda: led(1) # Turn off LED, it is inverted
                ]
    common.loop(setup_fn=setup_fns, loop_fn=[], callback=sub_cb, subtopic=[SUBTOPIC])

main()
```


(see [nightlamp.py](firmware/nightlamp/main.py))

# Logging example

This is what's received by the remote logging server

```
22:32:12,488  - [ALL_CURTAINS]: Moving curtains up for 3 sec
22:32:33,769  - [ALL_CURTAINS]: Receiving OTA update..
22:32:33,781  - [ALL_CURTAINS]: ['192.168.2.189', '1233', 'main.py', '819d7bf839af03c912af6e81f65ab404e5915ab5', '1']
22:32:33,788  - [ALL_CURTAINS]: Target IP: 192.168.2.189, Target Port: 1233, Local filename: main.py, hash: 819d7bf839af03c912af6e81f65ab404e5915ab5
22:32:34,023  - [ALL_CURTAINS]: renaming tmp to main.py
22:32:34,183  - [ALL_CURTAINS]: Restarting, as requested by OTA (or default)
22:32:39,433  - [ALL_CURTAINS]: Connected to SSID!
22:32:39,643  - [ALL_CURTAINS]: Subscribing to b'ALL_CURTAINS/set/#'
22:32:39,772  - [ALL_CURTAINS]: Subscribing to b'ALL_CURTAINS/OTA'
22:32:41,927  - [ALL_CURTAINS]: Moving curtains down for 3 sec
22:32:44,935  - [ALL_CURTAINS]: Done
22:35:51,629  - [NIGHTLAMP]: Publish 24.30 to b'TEMP/NIGHTLAMP'
22:35:51,629  - [NIGHTLAMP]: Publish 48.30 to b'HUM/NIGHTLAMP'
22:40:51,660  - [NIGHTLAMP]: Publish 24.30 to b'TEMP/NIGHTLAMP'
22:40:51,660  - [NIGHTLAMP]: Publish 48.30 to b'HUM/NIGHTLAMP'
22:45:51,765  - [NIGHTLAMP]: Publish 24.10 to b'TEMP/NIGHTLAMP'
22:45:51,765  - [NIGHTLAMP]: Publish 49.20 to b'HUM/NIGHTLAMP'
22:50:51,805  - [NIGHTLAMP]: Publish 25.00 to b'TEMP/NIGHTLAMP'
22:50:51,806  - [NIGHTLAMP]: Publish 47.20 to b'HUM/NIGHTLAMP'
```
