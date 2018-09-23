#!/usr/bin/env python3
import socket
import datetime

HOST = ''
PORT = 3333

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

try:
    s.bind((HOST, PORT))
except socket.error as msg:
    print('Bind failed. Error Code : ' + str(msg[0]) + ' Message ' + msg[1])
    exit(1)

try:
    while True:
        data, addr = s.recvfrom(1024) # buffer size is 1024 bytes
        msg = data.decode('ascii', 'ignore')
        sender = msg.split('|')[0]
        body = '|'.join(msg.split('|')[1:])
        print("[%s]: %s" % (sender, body))
except Exception as e:
    print(e)
    pass

s.close()
