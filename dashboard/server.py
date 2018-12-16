#!/usr/bin/env python3
import logging
import json
import mqtt_server
import ws_server
from threading import Thread
from queue import Queue

mqtt_q = Queue()
ws_q = Queue()
t = Thread(target=mqtt_server.serve, args=(mqtt_q, ws_q))
t.daemon = True
t.start()

t2 = Thread(target=ws_server.serve, args=(mqtt_q, ws_q))
t2.daemon = True
t2.start()

try:
    t.join()
    t2.join()
except KeyboardInterrupt:
    print("\nBye")
