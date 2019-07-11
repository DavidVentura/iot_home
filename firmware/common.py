import time
import usocket
import uos
from machine import Pin, reset
from network import WLAN, STA_IF, AP_IF
from mqtt import MQTTClient
from ubinascii import hexlify

MQTT_HOST = 'iot'
WIFI_CONNECTION_TIMEOUT = 10  # seconds
WIFI_SSID = 'cuevita'
WIFI_PASSWORD = 'salander'
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
        print("LOCAL-Connecting to Wi-Fi... %s" % WIFI_SSID)
        wifi_reconnect_time = time.time() + WIFI_CONNECTION_TIMEOUT
        STA.connect(WIFI_SSID, WIFI_PASSWORD)
        time.sleep_ms(10)

        while not STA.isconnected() and time.time() < wifi_reconnect_time:
            led.value(not led())
            print("LOCAL-Waiting wifi...")
            time.sleep_ms(1000)

        if not STA.isconnected():
            # reset device?
            print("LOCAL-Connection FAILED!")

    log("Connected to %s!" % WIFI_SSID)

def setup_wifi(CLIENT_ID):
    AP = WLAN(AP_IF)
    AP.active(False)

    STA = WLAN(STA_IF)
    STA.active(True)
    STA.config(dhcp_hostname=CLIENT_ID)
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

def mqtt_client(MQTT_HOST, callback, subtopic):
    assert type(subtopic) is list
    mqtt = MQTTClient(CLIENT_ID, MQTT_HOST)
    if callback:
        mqtt.set_callback(callback)
    connect_mqtt(mqtt)
    for topic in subtopic:
        log('Subscribing to %s' % topic)
        mqtt.subscribe(topic)
    return mqtt

def OTA_wrapper(callback):
    def OTA(topic, msg):
        if topic != OTA_TOPIC:
            callback(topic, msg)
            return

        log("Receiving OTA update..")
        if len(msg) < 45: # 40 is the length of the sha1
            log("Something wrong with the message")
            log(msg)
            return

        data = msg.decode('ascii').split("|")
        log(data)
        log("Target IP: %s, Target Port: %s, Local filename: %s, hash: %s" % tuple(data))
        success = receive_ota(data[0], int(data[1]), data[3])
        # ip, port, hash
        if not success:
            log("File transfer failed. Not overwriting local file.")
            return

        log("renaming tmp to %s" % data[2])
        uos.rename('tmp', data[2])

        reboot = True
        if len(data) == 5:
            reboot = bool(data[4])

        if reboot:
            log('Restarting, as requested by OTA (or default)')
            reset()
        else:
            log('Not restarting, as requested by OTA')
    return OTA

def receive_ota(host, port, remote_hash):
    import uhashlib
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
    local_hash = hexlify(_hash.digest()).decode('ascii')
    if local_hash != remote_hash:
        log("Got a bad file transfer? Hash mismatch")
        log("Local hash: %s, Remote hash: %s" % (local_hash, remote_hash))
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

def publish(topic, msg, retain=True, qos=0):
    if mqtt is not None:
        log('Publish %s to %s' % (msg, topic))
        mqtt.publish(topic, msg, retain, qos)
    else:
        log('Tried to publish but mqtt is not yet setup')

def get_client_id():
    if 'HOSTNAME' in uos.listdir('/'):
        return open('HOSTNAME', 'r').read().strip()
    mac = hexlify(WLAN().config('mac'),':').decode()
    return mac

def loop(_id=None, setup_fn=None, loop_fn=[], callback=None, subtopic=[]):
    global mqtt
    global OTA_TOPIC
    global CLIENT_ID
    CLIENT_ID = get_client_id()
    try:
        STA = setup_wifi(CLIENT_ID)
        OTA_TOPIC = ("%s/OTA" % CLIENT_ID).encode('ascii')
        mqtt = mqtt_client(MQTT_HOST, callback=OTA_wrapper(callback), subtopic=subtopic+[OTA_TOPIC])
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
        log('Resetting')
        reset()
