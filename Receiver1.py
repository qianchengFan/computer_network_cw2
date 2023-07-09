# Qiancheng Fan S1935167
import socket
import time
import sys
import math
import threading

messageSize = 1027

def receive(argv):
    port = argv[1]
    fileName = argv[2]

    # initialise the receiver socket
    receiverSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    receiverSocket.bind(('', int(port)))

    # open file for write
    w = open(fileName, 'wb')
    msg = bytearray(receiverSocket.recv(messageSize))
    while receiverSocket:
        sequence = msg[0:2]
        eof = msg[2]
        payload = msg[3:]
        if (eof == 0):
            w.write(payload)  # write to file
            msg = bytearray(receiverSocket.recv(messageSize))  # read next packet
        else:
            w.write(payload)
            w.close()
            break


if __name__ == '__main__':
    receive(sys.argv)
