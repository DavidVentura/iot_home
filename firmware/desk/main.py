import common
import time
import dht

from machine import Pin

from desk import Desk

CLIENT_ID = 'DESK'
SUBTOPIC = b"%s/set" % CLIENT_ID
PUBTOPIC = b"%s/state" % CLIENT_ID

d = None

def sub_cb(topic, msg):
    try:
        value = int(msg)
    except Exception as e:
        common.log(e)
        return
    common.log("Moving to %s" % value)
    d.move_to(value)

@common.debounce(300_000)
def read_desk():
    d.read_height(lambda height: common.publish(PUBTOPIC, str(int(height))))

def setup():
    global d
    print("Main starting")
    d = Desk(b'\xe6\xcc\xe3W\x9aA')
    print("Connected")

def main():
    common.loop(setup_fn=setup, loop_fn=[read_desk], callback=sub_cb, subtopic=[SUBTOPIC])

main()
