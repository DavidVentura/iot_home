from machine import Pin
from network import WLAN, STA_IF
from mqtt import MQTTClient
import time

MQTT_HOST = 'iot'
WIFI_CONNECTION_TIMEOUT = 10  # seconds
WIFI_SSID = 'cuevita'
WIFI_PASSWORD = 'salander'
PUBLISH_INTERVAL = 60 # seconds
OTA_TOPIC = b'OTA'

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
            time.sleep_ms(1000)

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
    mqtt.subscribe(OTA_TOPIC)
    if subtopic:
        mqtt.subscribe(subtopic)
    return mqtt

def OTA_wrapper(callback):
    def OTA(topic, msg):
        if topic != OTA_TOPIC:
            callback(topic, msg)
            return

        if len(msg) < 45: # 40 is the length of the sha1
            print("Something wrong with the message")
            print(msg)
            return

        data = msg.decode('ascii').split("|")
        print(data)
        success = receive_ota(data[0], int(data[1]), data[3])
        # ip, port, hash
        if not success:
            return

        import machine
        import uos
        print("renaming tmp to %s" % data[2])
        uos.rename('tmp', data[2])
        print('restarting')
        machine.reset()
    return OTA

def receive_ota(host, port, remote_hash):
    import uhashlib
    import ubinascii
    import usocket
    sockaddr = usocket.getaddrinfo(host, port)[0][-1]
    # You need this object even for numeric addresses

    sock = usocket.socket()
    sock.connect(sockaddr)
    f = open('tmp', 'wb') # write the streamed data to a file
    # as we might not have enough memory for the entire thing
    # also calculate hash while streaming
    _hash = uhashlib.sha1()
    while True:
        d = sock.recv(1024)
        if len(d) == 0:
            break
        _hash.update(d)
        f.write(d)
    sock.close()
    f.close()
    local_hash = ubinascii.hexlify(_hash.digest()).decode('ascii')
    if local_hash != remote_hash:
        print(local_hash)
        return False

    return True

def loop(client_id, setup_fn, loop_fn, callback, subtopic):
    global mqtt
    STA = setup_wifi()
    mqtt = mqtt_client(client_id, MQTT_HOST, callback=OTA_wrapper(callback), subtopic=subtopic)
    for f in setup_fn:
        f()
    while True:
        if not STA.isconnected():
            connect_wifi(STA)
        for f in loop_fn:
            f()
        time.sleep_ms(200)
        mqtt.check_msg()
    mqtt.disconnect()
