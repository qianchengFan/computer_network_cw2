#Qiancheng Fan 1935167
import socket
import time
import sys
import math
import threading

payloadSize = 1024
numRet=0 # resend counter
ackRec = [] # used to store received ack
last_ack = None

def receiveACK(socket):
    while True:
        global ackRec
        global last_ack
        byteAck= socket.recv(2)
        last_ack = int.from_bytes(byteAck, 'big')
        ackRec.append(last_ack)

def send(argv):
    global ackRec
    global last_ack
    global numRet
    host = argv[1]
    port = int(argv[2])
    path = argv[3]
    timeout = int(argv[4])/1000
    # start timer, used to calculate throughput
    start = time.time()

    # initialise sender socket
    senderSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # read file
    with open(path, 'rb') as f:
        file_content = bytearray(f.read())
    filesize = len(file_content)/1024
    startPoint = 0
    sequence = 0
    next_file = file_content[:1024]

    # start ack receiver thread
    receive_thread = threading.Thread(target=receiveACK, args=(senderSocket,))
    receive_thread.setDaemon(True)
    receive_thread.start()

    while (next_file):
        global ackRec
        byteSequence = sequence.to_bytes(2, byteorder='big')
        intSequence = int.from_bytes(byteSequence,'big')
        sequence += 1
        msg = bytearray()
        msg [0:2] = byteSequence # sequence number

        # if not end of file
        if (len(next_file)>=payloadSize):
            eof = (0).to_bytes(1,byteorder='big')
            msg[2:3] = eof
            msg[3:] = next_file
            senderSocket.sendto(msg, (host, port))

            #print("send %d" %int.from_bytes(byteSequence,'big'))

            start_time = time.time() # timer for timeout
            while int.from_bytes(byteSequence,'big') not in ackRec:
                current = time.time()
                time.sleep(0)
                if current-start_time > timeout: # if timeout, resend count +1, and resend the packet
                    senderSocket.sendto(msg, (host, port))
                    numRet += 1
                    start_time = time.time()

        # if end of file
        else:
            eof = (1).to_bytes(1,byteorder='big')
            msg[2:3] = eof
            msg[3:] = next_file
            senderSocket.sendto(msg, (host, port))

            start_time = time.time() # timer for timeout
            while int.from_bytes(byteSequence,'big') not in ackRec:
                if time.time()-start_time > timeout:
                    senderSocket.sendto(msg, (host, port))
                    numRet += 1
                    start_time = time.time() # if timeout, resend count +1, and resend the packet

            end = time.time() # send finish time
            ret_count = str(numRet)
            throughout = str(round(filesize/(end-start)))
            print(ret_count + " " + throughout)
            break

        # load next packet
        startPoint +=1024
        next_file = file_content[startPoint:startPoint+1024]


if __name__ == '__main__':
    send(sys.argv)