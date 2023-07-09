#Qiancheng Fan S1935167
import socket
import time
import sys
import math
import threading

messageSize = 1027

def receive(argv):
    sequenceReceived = []
    port = argv[1]
    fileName = argv[2]
    windows_size = int(argv[3])

    # initialise receiver socket
    receiverSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    receiverSocket.bind(('',int(port)))

    # open file for write
    w = open(fileName,'wb+')

    # read the first packet
    msg,senderAdd = receiverSocket.recvfrom(messageSize)
    current_seq = 0
    next_seq = 0
    cache = {} # cache used to store packets in windows size
    write=[] # record which sequence already writed
    while receiverSocket:
        byteSequence = msg[0:2]
        eof = msg[2]
        payload = msg[3:]

        # if the packet in windows size
        if (int.from_bytes(byteSequence,'big') <= (current_seq + windows_size)):
            receiverSocket.sendto(byteSequence, senderAdd)
            #print("sent ack %d" %int.from_bytes(byteSequence,'big'))

            # if the packet is the one we want to write
            if (int.from_bytes(byteSequence,'big')==current_seq):
                w.write(payload)
                write.append(payload)

                #print("write %d"%int.from_bytes(byteSequence,'big'))

                # sent last ack multiple times to prevent ack lost but receiver closed
                if(eof == 1):
                    w.close()
                    receiverSocket.sendto(byteSequence, senderAdd)
                    receiverSocket.sendto(byteSequence, senderAdd)
                    receiverSocket.sendto(byteSequence, senderAdd)
                    receiverSocket.sendto(byteSequence, senderAdd)
                    sys.exit()
                current_seq += 1

                # write valid packets in cache to file, and remove it out of cache
                while cache:
                    if str(current_seq) in cache:
                        w.write(cache[str(current_seq)][0])
                        if(cache[str(current_seq)][1])==1:
                            sys.exit()
                        write.append(cache[str(current_seq)])
                        del cache[str(current_seq)]
                        current_seq += 1
                    else:
                        break

            else:
                # is the packet not in order but in windows size, write it to cache
                cache[str(int.from_bytes(byteSequence,'big'))] = [payload,eof]
        # read next packet
        msg, senderAdd = receiverSocket.recvfrom(messageSize)
if __name__ == '__main__':
    receive(sys.argv)
