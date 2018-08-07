import hashlib
import os
import socket
import sys
import paho.mqtt.publish as publish

PORT = 1234
HOSTNAME = socket.gethostname()

def main(_file, fname=None):
    content = open(_file, 'r', encoding='ascii').read()
    sha1 = hashlib.sha1(content.encode('ascii')).hexdigest()

    if fname is None:
        fname = os.path.basename(_file)

    payload = "{hostname}|{port}|{filename}|{hash}".format(hash=sha1, filename=fname, hostname=HOSTNAME, port=PORT)

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', PORT))
    s.settimeout(5)
    s.listen(1)
    
    print(payload)
    publish.single('OTA', payload, hostname='iot')
    conn, addr = s.accept()
    with conn:
        print("Connected!")
        conn.sendall(content.encode('ascii'))

if __name__ == '__main__':
    fname = sys.argv[1]
    if not os.path.isfile(fname):
        print("%s doesnt exist / is not afile" % fname)
        sys.exit(1)
    main(fname)
