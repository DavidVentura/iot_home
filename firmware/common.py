from machine import Pin, reset
from network import WLAN, STA_IF
from mqtt import MQTTClient
import time
import usocket

MQTT_HOST = 'iot'
WIFI_CONNECTION_TIMEOUT = 10  # seconds
WIFI_SSID = 'cuevita'
WIFI_PASSWORD = 'salander'
PUBLISH_INTERVAL = 60 # seconds
OTA_TOPIC = None
CLIENT_ID = "ID_NOT_SET"
LOGSERVER = '192.168.2.189'

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
        print("LOCAL-Connecting to Wi-Fi...")
        wifi_reconnect_time = time.time() + WIFI_CONNECTION_TIMEOUT
        STA.connect(WIFI_SSID, WIFI_PASSWORD)

        while not STA.isconnected() and time.time() < wifi_reconnect_time:
            led.value(not led())
            print("LOCAL-Waiting wifi...")
            time.sleep_ms(1000)

        if not STA.isconnected():
            print("LOCAL-Connection FAILED!")
    log("Connected!")

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
            log(e)
            time.sleep_ms(200)

def mqtt_client(MQTT_HOST, callback=None, subtopic=None):
    mqtt = MQTTClient(CLIENT_ID, MQTT_HOST)
    if callback:
        mqtt.set_callback(callback)
    connect_mqtt(mqtt)
    mqtt.subscribe(OTA_TOPIC)
    if subtopic is not None:
        if type(subtopic) is list:
            for topic in subtopic:
                mqtt.subscribe(topic)
        else:
            mqtt.subscribe(subtopic)
    return mqtt

def OTA_wrapper(callback):
    def OTA(topic, msg):
        if topic != OTA_TOPIC:
            callback(topic, msg)
            return

        if len(msg) < 45: # 40 is the length of the sha1
            log("Something wrong with the message")
            log(msg)
            return

        data = msg.decode('ascii').split("|")
        log(data)
        success = receive_ota(data[0], int(data[1]), data[3])
        # ip, port, hash
        if not success:
            return

        import machine
        import uos
        log("renaming tmp to %s" % data[2])
        uos.rename('tmp', data[2])
        log('restarting')
        machine.reset()
    return OTA

def receive_ota(host, port, remote_hash):
    import uhashlib
    import ubinascii
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
        log(local_hash)
        return False

    return True

def log(msg):
    print(msg)
    try:
        s = usocket.socket(usocket.AF_INET, usocket.SOCK_DGRAM)
        address = (LOGSERVER, 3333)
        s.connect(address)
        s.send("%s|%s" % (CLIENT_ID, msg))
    except Exception as e:
        print(e)

def loop(_id, setup_fn, loop_fn, callback, subtopic):
    global mqtt
    global OTA_TOPIC
    global CLIENT_ID
    CLIENT_ID = _id
    try:
        OTA_TOPIC = ("%s/OTA" % CLIENT_ID).encode('ascii')
        STA = setup_wifi()
        mqtt = mqtt_client(MQTT_HOST, callback=OTA_wrapper(callback), subtopic=subtopic)
        if setup_fn is not None:
            setup_fn()
        while True:
            if not STA.isconnected():
                connect_wifi(STA)
            for f in loop_fn:
                f()
            time.sleep_ms(100)
            mqtt.check_msg()
        mqtt.disconnect()
    except Exception as e:
        log(e)
        reset()
