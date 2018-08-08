#!/usr/bin/env python3
import argparse
import hashlib
import os
import socket
import sys
import paho.mqtt.publish as publish

PORT = 1234
HOSTNAME = socket.gethostname()

def main(_file, fname, target):
    content = open(_file, 'r', encoding='ascii').read()
    sha1 = hashlib.sha1(content.encode('ascii')).hexdigest()

    if fname is None:
        fname = os.path.basename(_file)

    payload = "{hostname}|{port}|{filename}|{hash}".format(hash=sha1, filename=fname, hostname=HOSTNAME, port=PORT)

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
    parser.add_argument("--target", required=True, help="Target CLIENT_ID, case sensitive")
    args = parser.parse_args()
    if not os.path.isfile(args.file):
        print("%s doesnt exist / is not afile" % fname)
        sys.exit(1)
    main(args.file, args.as_file, args.target)
