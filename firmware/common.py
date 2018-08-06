from machine import Pin
from network import WLAN, STA_IF
from mqtt import MQTTClient
import time

MQTT_HOST = 'iot'
WIFI_CONNECTION_TIMEOUT = 10  # seconds
WIFI_SSID = 'cuevita'
WIFI_PASSWORD = 'salander'
PUBLISH_INTERVAL = 60 # seconds

led = Pin(13, Pin.OUT)
_debounce = {}
mqtt = None

def debounce(interval):
    def cdecorator(func):
        def wrapper(*args, **kwargs):
            fname = repr(func).split(" ")[1]
            # FIXME hack until I can use __name__
            if fname not in _debounce:
                _debounce[fname] = -interval
            delta = time.ticks_diff(time.ticks_ms(), _debounce[fname])
            if delta < interval:
                return
            _debounce[fname] = time.ticks_ms()
            func(*args, **kwargs)
        return wrapper
    return cdecorator

def connect_wifi(STA):
    while not STA.isconnected():
        print("Connecting to Wi-Fi...")
        wifi_reconnect_time = time.time() + WIFI_CONNECTION_TIMEOUT
        STA.connect(WIFI_SSID, WIFI_PASSWORD)

        while not STA.isconnected() and time.time() < wifi_reconnect_time:
            led.value(not led())
            print("Waiting wifi...")
            time.sleep_ms(500)

        if not STA.isconnected():
            print("Connection FAILED!")
    print("Connected!")

def setup_wifi():
    STA = WLAN(STA_IF)
    STA.active(True)
    connect_wifi(STA)
    return STA

def connect_mqtt(m):
    while True:
        try:
            m.connect()
            return
        except Exception as e:
            led.value(not led())
            print(e)
            time.sleep_ms(200)

def mqtt_client(CLIENT_ID, MQTT_HOST, callback=None, subtopic=None):
    mqtt = MQTTClient(CLIENT_ID, MQTT_HOST)
    if callback:
        mqtt.set_callback(callback)
    connect_mqtt(mqtt)
    if subtopic:
        mqtt.subscribe(subtopic)
    return mqtt

def loop(client_id, setup_fn, loop_fn, callback, subtopic):
    global mqtt
    STA = setup_wifi()
    mqtt = mqtt_client(client_id, MQTT_HOST, callback=callback, subtopic=subtopic)
    for f in setup_fn:
        f()
    while True:
        if not STA.isconnected():
            connect_wifi()
        for f in loop_fn:
            f()
        time.sleep_ms(200)
        mqtt.check_msg()
    mqtt.disconnect()
