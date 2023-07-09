# Qiancheng Fan S1935167
import socket
import time
import sys
import math
import threading

exit_flag = False
ackRec = []
payloadSize = 1024
ack = 0
numRet = 0
last_base = 0
totalFileSize = 0
last_ack = -1
timers = []
timer = 9999999
base_seq = 0
next_seq = 0
last_seq = 99999
start_time = time.time()
printed = False
last_ack_time = time.time()


def receiveACK(socket):
    global ackRec
    global totalFileSize
    global last_ack
    global base_seq
    global next_seq
    global timer
    global last_ack
    global last_seq
    global start_time
    global ackRec
    global exit_flag
    global last_ack_time

    while True:
        # use try to prevent stuck
        try:
            byteAck, address = socket.recvfrom(2)  # recv 2 bytes for ack
            last_ack_time = time.time()
        except Exception:
            if last_seq in ackRec:
                exit_flag = True
                break
            continue

        # create a int value of the 2 bytes ack, since int is easier to compare
        last_ack = int.from_bytes(byteAck, 'big')

        if last_ack not in ackRec:
            ackRec.append(last_ack)  # add new ack to ack record list
        # print("ack ",last_ack,"base",base_seq,"next",next_seq)
        time.sleep(0.00001)

        # The receiver only will write payload in continuous sequence
        # so if a returned ack is higher than base sequence, it must
        # because of some ack lost, so we just change base sequence
        # to the largest ack we receive
        if last_ack > base_seq:
            base_seq = last_ack + 1
            timer = time.time()
            # update the ack record list also
            for i in range(last_ack - base_seq + 1):
                ackRec.append(base_seq + i - 1)
            continue

        if last_ack == base_seq:
            base_seq += 1
            if base_seq == next_seq:
                timer = 999999999  # stop the timer
            else:
                timer = time.time()  # start timer


def send(argv, senderSocket):
    global totalFileSize
    global last_ack
    global timer
    global base_seq
    global next_seq
    global last_seq
    global start_time
    global exit_flag
    global last_base
    global printed
    global last_ack_time
    totalFileSize = 0
    host = argv[1]
    port = int(argv[2])
    path = argv[3]
    timeout = int(argv[4]) / 1000
    window_size = int(argv[5])
    # retry=0
    ackSent=[]

    # used to handle stuck that caused by ack lost later
    stuck_count = 0
    stuck_time = None

    # open file to read
    with open(path, 'rb') as f:
        file_content = bytearray(f.read())
    # calculate the total file size to calculate throughput later
    file_size = len(file_content) / 1024
    totalFileSize = file_size

    # pick first part of the file
    next_file = file_content[:1024]

    # initial start time, used to calculate throughput later
    start_time = time.time()

    while next_file:
        global ackRec

        # while next sequence in windows size and valid
        while next_seq < base_seq + window_size and next_seq < math.ceil(len(file_content) / 1024):

            # set up the message of next_sequence to be sent
            start_point = next_seq * 1024
            next_file = file_content[start_point:(start_point + 1024)]
            byteSequence = next_seq.to_bytes(2, byteorder='big')
            intSequence = int.from_bytes(byteSequence, 'big')
            if len(next_file) < 1024:
                eof = 1
            else:
                eof = 0
            msg = bytearray()
            msg[0:2] = byteSequence
            msg[2:3] = eof.to_bytes(1, byteorder='big')
            msg[3:] = next_file

            # send the packet
            senderSocket.sendto(msg, (host, port))
            ackSent.append(intSequence)

            # for testing only.
            # if intSequence in ackSent:
            #     retry+=1

            if intSequence == 0:  # Just in case
                senderSocket.sendto(msg, (host, port))
                senderSocket.sendto(msg, (host, port))
                senderSocket.sendto(msg, (host, port))

            if (base_seq == next_seq):
                timer = time.time() # start timer

            # inc next sequence
            next_seq += 1

            # print("send ",intSequence,"eof",int.from_bytes(msg[2:3],'big'),"base",base_seq,"next",next_seq)
            time.sleep(0.00001)

            # check whether last ack received, if it is , all files are sent, close the program
            if last_seq in ackRec:
                # print("last seq is ",last_seq)
                time.sleep(0)
                exit_flag = True
                print(totalFileSize / (time.time() - start_time))
                # print(retry)
                printed = True
                sys.exit()

            # if last packet has been sent at least once, make a record
            if eof == 1:
                last_seq = intSequence

        # make sure next seq not beyond the file size and accidentally make the loop end
        if next_seq >= math.ceil(len(file_content) / 1024):
            next_seq -= 1

        # stuck handler, just in case of ack lost，receiver closed.
        if last_seq != 99999:
            if base_seq == last_base:
                stuck_count += 1
            else:
                stuck_time = time.time()
                stuck_count = 0
                last_base = base_seq

            if stuck_count >= 1000:
                if time.time() - last_ack_time > 2:
                    exit_flag = True
                    if stuck_time != None:
                        print(totalFileSize / (time.time() - 2 - start_time))

                    # just in case, it will not happen
                    else:
                        print(totalFileSize / (time.time() - 2 - start_time))

                # print("stuck")
                time.sleep(0)
                # print("stuck handled")
                printed = True
                if exit_flag == True:
                    sys.exit()


if __name__ == '__main__':
    timeout = int(sys.argv[4]) / 1000
    # initialise socket and thread
    senderSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    receive_thread = threading.Thread(target=receiveACK, args=(senderSocket,))
    receive_thread.setDaemon(True)
    send_thread = threading.Thread(target=send, args=(sys.argv, senderSocket))
    receive_thread.start()
    send_thread.start()

    # give thread some time to start
    time.sleep(0.1)

    # timer loop
    timer = time.time()
    while True:
        time.sleep(0)
        if exit_flag == True:
            sys.exit()
        elif time.time() - timer > timeout:
            # print(time.time()-timer)
            # print("timeout")
            time.sleep(0.00001)
            next_seq = base_seq
            timer = time.time()

    receive_thread.join()
    send_thread.join()

    # just in case, normally will not be used
    if not printed:
        print(totalFileSize / (time.time() - start_time))