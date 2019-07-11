#!/usr/bin/env python3
import argparse
import hashlib
import os
import socket
import sys
import paho.mqtt.publish as publish

PORT = 1233
HOSTNAME = socket.gethostname()

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(('8.8.8.8', 53))
localip = s.getsockname()[0]
s.close()

HOSTNAME = localip # my notebook does not get resolved for some reason

def main(_file, fname, target, reboot=False):
    content = open(_file, 'r', encoding='ascii').read()
    sha1 = hashlib.sha1(content.encode('ascii')).hexdigest()

    if fname is None:
        fname = os.path.basename(_file)

    payload = "{hostname}|{port}|{filename}|{hash}".format(hash=sha1, filename=fname, hostname=HOSTNAME, port=PORT, reboot=int(reboot))
    payload = "{hostname}|{port}|{filename}|{hash}|{reboot}".format(hash=sha1, filename=fname, hostname=HOSTNAME, port=PORT, reboot=int(reboot))

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('', PORT))
    s.settimeout(3)
    s.listen(1)
    
    print("Publishing to %s the file %s (as %s) on %s:%s" % (target, _file, fname, HOSTNAME, PORT))
    publish.single('%s/OTA' % target, payload, hostname='iot')
    #publish.single('OTA', payload, hostname='iot')
    try:
        conn, addr = s.accept()
    except socket.timeout:
        print("Timed out!")
        return

    with conn:
        print("Connected!")
        conn.sendall(content.encode('ascii'))
    print("Finished")
    s.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("file")
    parser.add_argument("--as-file", required=False)
    parser.add_argument("--reboot", action='store_true')
    parser.add_argument("--target", required=True, help="Target hostname, case sensitive")
    args = parser.parse_args()
    if not os.path.isfile(args.file):
        print("%s does not exist / is not a file" % fname)
        sys.exit(1)

    print(args.reboot)
    main(args.file, args.as_file, args.target, args.reboot)
