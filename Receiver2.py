# Qiancheng Fan S1935167
import socket
import time
import sys
import math
import threading

messageSize = 1027


def receive(argv):
    sequenceReceived = []  # used to make sure dont write duplicate packet again
    port = argv[1]
    fileName = argv[2]
    receiverSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # used to receive packet
    receiverSocket.bind(('', int(port)))
    w = open(fileName, 'wb')  # open file to write
    msg, senderAdd = receiverSocket.recvfrom(messageSize)  # get data through socket
    while receiverSocket:
        byteSequence = msg[0:2]
        eof = msg[2]
        payload = msg[3:]

        # print("rec",int.from_bytes(byteSequence,'big'))
        receiverSocket.sendto(byteSequence, senderAdd)  # send ack back
        # print("sent", int.from_bytes(byteSequence, 'big'))

        if not sequenceReceived.__contains__(byteSequence):  # write non-duplicate packet
            sequenceReceived.append(byteSequence)  # add sequence number to received sequence list
            if (eof == 0):
                w.write(payload)
            else:
                w.write(payload)
                # send last ack back 5 times to avoid the case that the last packet recived
                # and the receiver closed, but last ack lost and the sender keep sending last
                # packet forever because if didn't receive ack.
                receiverSocket.sendto(byteSequence, senderAdd)
                receiverSocket.sendto(byteSequence, senderAdd)
                receiverSocket.sendto(byteSequence, senderAdd)
                receiverSocket.sendto(byteSequence, senderAdd)
                receiverSocket.sendto(byteSequence, senderAdd)
                w.close()
                sys.exit()
        msg, senderAdd = receiverSocket.recvfrom(messageSize)  # read next packet

if __name__ == '__main__':
    receive(sys.argv)
