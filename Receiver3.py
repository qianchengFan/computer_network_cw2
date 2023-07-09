#Qiancheng Fan S1935167
import socket
import time
import sys
import math
import threading

messageSize = 1027
current_ack=0
seqRec = []
def receive(argv):
    port = argv[1]
    fileName = argv[2]

    # initialise receiver socket
    receiverSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    receiverSocket.bind(('',int(port)))

    # open file for write
    w = open(fileName,'wb')

    # read the first packet
    msg,senderAdd = receiverSocket.recvfrom(messageSize)
    while receiverSocket:
        global current_ack
        # take data out
        byteSequence = msg[0:2]
        intSequence = int.from_bytes(byteSequence, 'big')
        eof = msg[2:3]
        payload = msg[3:]

        # if the sequence received is the one we want
        if intSequence == current_ack:

            # send ack back and write to file
            receiverSocket.sendto(byteSequence, senderAdd)
            w.write(payload)

            # print('write',intSequence,"eof",int.from_bytes(eof,'big'))
            current_ack+=1

            # send last ack many times to prevent last packet lost but receiver closed
            if len(payload)<1024 or eof==(1).to_bytes(1,'big'):
                # print("end reached")
                receiverSocket.sendto(byteSequence, senderAdd)
                receiverSocket.sendto(byteSequence, senderAdd)
                receiverSocket.sendto(byteSequence, senderAdd)
                receiverSocket.sendto(byteSequence, senderAdd)
                receiverSocket.sendto(byteSequence, senderAdd)
                w.close()
                sys.exit()

        # if the sequence received is not what we want,
        # sent 0 or the previous sequence to sender
        else:
            if(current_ack != 0):
                ack = (current_ack-1).to_bytes(2,'big')
                receiverSocket.sendto(ack, senderAdd)
            else:
                ack = (0).to_bytes(2, 'big')
                receiverSocket.sendto(ack, senderAdd)
        msg, senderAdd = receiverSocket.recvfrom(messageSize)

if __name__ == '__main__':
    receive(sys.argv)

