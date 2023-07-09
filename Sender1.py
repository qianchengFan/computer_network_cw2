# Qiancheng Fan S1935167
import socket
import time
import sys
import math
import threading

payloadSize = 1024


def send(argv):
    host = argv[1]
    port = int(argv[2])
    path = argv[3]

    # initialise sender socket
    senderSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # open file for read
    with open(path, 'rb') as f:
        file_content = bytearray(f.read())

    # read the whole file then split the file to packets
    # by using start point, take 1024 bytes each time.
    startPoint = 0
    sequence = 0
    next_file = file_content[:1024]
    while (next_file):
        byteSequence = sequence.to_bytes(2, byteorder='big')
        sequence += 1
        msg = bytearray()
        msg[0:2] = byteSequence  # sequence number

        if (len(next_file) >= payloadSize):
            eof = (0).to_bytes(1, byteorder='big')
            msg[2:3] = eof  # eof 0
            msg[3:] = next_file  # payload
            senderSocket.sendto(msg, (host, port))
            time.sleep(0.001)
        else:
            eof = (1).to_bytes(1, byteorder='big')
            msg[2:3] = eof  # eof 1
            msg[3:] = next_file  # payload
            senderSocket.sendto(msg, (host, port))
            break

        # load next packet
        startPoint += 1024
        next_file = file_content[startPoint:startPoint + 1024]


if __name__ == '__main__':
    send(sys.argv)
