import asyncio
import datetime
import logging
import json
from threading import Thread
from websocket_server import WebsocketServer

state = {}
def new_client(client, server):
	server.send_message_to_all(json.dumps(state))

def msg_received(q):
    def wrap(client, server, msg):
        try:
            msg = json.loads(msg)
        except:
            print("Got invalid json from client (%s)" % msg)
            return
        print("Got %s from a ws client; putting to queue" % msg)
        q.put(msg)
    return wrap

def serve(mqtt_q, ws_q):
    server = WebsocketServer(8998, host='0.0.0.0') #, loglevel=logging.INFO)
    server.set_fn_new_client(new_client)
    server.set_fn_message_received(msg_received(ws_q))
    t = Thread(target=server.run_forever)
    t.daemon = True
    t.start()
    while True:
        topic, msg = mqtt_q.get()
        print("< %s, %s" % (topic,msg))
        state[topic] = msg
        tstamp = datetime.datetime.now().strftime("%H:%M:%S")
        state['timestamp'] = tstamp
        server.send_message_to_all(json.dumps({topic: msg, "timestamp": tstamp}))
    t.join()
