import common
from machine import Pin, PWM
from encoder import Encoder

MAX_STEPS_ENCODER = 32
CLIENT_ID = 'LIGHTS'
SUBTOPIC = b"%s/set/#" % CLIENT_ID
PUBTOPIC_ON = b"%s/state/power" % CLIENT_ID
PUBTOPIC_VALUE = b"%s/state/intensity" % CLIENT_ID

light_pin = Pin(14) # D5
light_pwm = PWM(light_pin, freq=1000)
light_pwm.duty(512) # 0 = 0%, 1023 = 100%
sw = Pin(5, Pin.IN, Pin.PULL_UP) # d1

light_intensity = 1
light_on = True


def set_light(on, value):
    light_pwm.duty(on * value)
    common.publish(PUBTOPIC_ON, str(on))
    common.publish(PUBTOPIC_VALUE, str(value))

def update_light():
    value =  light_intensity * int(1024/MAX_STEPS_ENCODER)
    set_light(int(light_on), value)

@common.debounce(250)
def btn_callback(p):
    global light_on
    common.log('btn change %s' % p)
    light_on = not light_on
    update_light()

def rotary_cb(value):
    global light_intensity
    common.log("rotary_change %s" % value)
    light_intensity = value
    update_light()

def sub_cb(topic, msg):
    global light_intensity
    global light_on
    topic = topic.decode('ascii')
    msg = msg.decode('ascii')
    print(topic, msg)
    if topic == '%s/set/INTENSITY' % CLIENT_ID:
        light_intensity = int(msg)
        e.override_value(light_intensity)
        update_light()
    elif topic == '%s/set/STATE' % CLIENT_ID:
        light_on = bool(msg)
        update_light()
    else:
        common.log("I got %s .. ?" % str(topic, msg))

def setup():
    global light_intensity
    global light_on
    light_intensity = 1
    light_on = True
    update_light()
    sw.irq(trigger=Pin.IRQ_FALLING, handler=btn_callback)

def main():
    common.loop(setup_fn=setup, loop_fn=[], callback=sub_cb, subtopic=[SUBTOPIC])

e = Encoder(4, 0, min_val=1, max_val=MAX_STEPS_ENCODER, callback=rotary_cb) # d2, d3 => order matters for rotation direction
main()
