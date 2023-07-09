#Qiancheng Fan S1935167
import socket
import time
import sys
import math
import threading

payloadSize = 1024
last_ack_time = time.time()
ack = 0
ackRec = []
stuck_time = None
last_seq = 99999
last_base = 0
numRet = 0
totalFileSize = 0
last_ack = None
flag = False
timers = []
sent = []

class timerClass(threading.Thread):
    def __init__(self, timeout, seq, eof, payload):
        super().__init__()
        self.timeout = False
        self.timeout_time = timeout
        self.seq = seq
        self.eof = eof
        self.payload = payload

    def run(self):
        time.sleep(self.timeout_time)
        self.timeout = True

    def reset(self):
        self.timeout = False

    def getTimeout(self):
        return self.timeout

    def get_seq(self):
        return self.seq

# similar to sender3's receiver thread
def receiveACK(socket):
    global ackRec
    global totalFileSize
    global last_ack
    global last_ack_time
    while True:
        # use try to prevent stuck
        try:
            byteAck, address = socket.recvfrom(2)  # recv 2 bytes for ack
            last_ack_time = time.time()
        except Exception:
            if last_seq in ackRec:
                break
            continue

        if (int.from_bytes(byteAck, 'big') != last_ack):
            last_ack = int.from_bytes(byteAck, 'big')
            if last_ack not in ackRec:
                ackRec.append(last_ack)

def send(argv):
    global totalFileSize
    global last_ack
    global flag
    global last_seq
    global last_base
    global last_ack_time
    global stuck_time
    host = argv[1]
    port = int(argv[2])
    path = argv[3]
    timeout = int(argv[4]) / 1000
    window_size = int(argv[5])
    exit_flag = False
    senderSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    base_seq = 0
    next_seq = 0

    # read file, calculate filesize, start timer for whole sending process
    with open(path, 'rb') as f:
        file_content = bytearray(f.read())
    size = int(len(file_content)/1024)
    start = time.time()
    next_file = file_content[:1024]# read first packet

    # start receiver thread
    receive_thread = threading.Thread(target=receiveACK, args=(senderSocket,))
    receive_thread.setDaemon(True)
    receive_thread.start()

    stuck_count = 0 # initialise stuck count for stuck handler
    while next_file:
        global last_ack
        global timers
        global ackRec
        global sent

        # while packet is valid and in windows size
        while next_seq < base_seq + window_size and next_seq < math.ceil(len(file_content) / 1024):
            global last_ack
            global sent

            # set up packet
            start_point = next_seq * 1024
            next_file = file_content[start_point:(start_point + 1024)]
            byteSequence = next_seq.to_bytes(2, byteorder='big')
            intSequence = int.from_bytes(byteSequence, 'big')
            if len(next_file) < 1024:
                eof = 1
                last_seq = intSequence
            else:
                eof = 0
            msg = bytearray()
            msg[0:2] = byteSequence
            msg[2:3] = eof.to_bytes(1, byteorder='big')
            msg[3:] = next_file

            # if haven't sent, send it and start timer
            if intSequence not in sent:
                sent.append(intSequence)
                senderSocket.sendto(msg, (host, port))
                # print("sent %d" % intSequence,"base",base_seq,'ack',last_ack,"len",len(msg))
                t = timerClass(timeout, intSequence, eof, next_file)
                t.start()
                timers.append(t)
            else:
                # check if all packet sent and received ack
                if last_seq in ackRec:
                    out_flag = True
                    for i in range(window_size-1):
                        if last_seq-i not in ackRec:
                            out_flag = False
                    if out_flag == True:
                        print(size/(time.time()-start))
                        sys.exit()

            # stuck handler, just in case receiver closed but ack lost.
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
                        print(size / (time.time() - 2 - start))

                    # just in case, it will not happen
                    else:
                        print(size / (time.time() - 2 - start))

                if(exit_flag == True):
                    sys.exit()
            next_seq+=1

        while True:
            if base_seq in ackRec:
                base_seq += 1
            else:
                break

        # check if any timer timeout, if is, resend packet and restart timer, else,
        # if ack received, remove the timer from timer list.
        for i in timers:
            if i.timeout == True:
                if i.seq < base_seq:
                    timers.remove(i)
                else:
                    if i.seq not in ackRec:
                        msg = bytearray()
                        msg[0:2] = i.seq.to_bytes(2, byteorder='big')
                        msg[2:3] = i.eof.to_bytes(1, byteorder='big')
                        msg[3:] = i.payload
                        timers.remove(i)
                        senderSocket.sendto(msg, (host, port))
                        t = timerClass(timeout, i.seq, i.eof, i.payload)
                        t.start()
                        timers.append(t)

        # make sure next seq not beyond the file size and accidentally make the loop end
        if (next_seq < math.ceil(len(file_content) / 1024)):
            start_point = next_seq * 1024
            next_file = file_content[start_point:(start_point + 1024)]
        else:
            next_seq = next_seq - 1
            start_point = next_seq * 1024
            next_file = file_content[start_point:]

        # if only last packet haven't receive ack, do this and exit
        if base_seq == math.ceil(len(file_content) / 1024):
            msg = bytearray()
            msg[0:2] = next_seq.to_bytes(2, 'big')
            msg[2:3] = (1).to_bytes(1, byteorder='big')
            msg[3:] = next_file
            senderSocket.sendto(msg, (host, port))
            senderSocket.sendto(msg, (host, port))
            senderSocket.sendto(msg, (host, port))
            senderSocket.sendto(msg, (host, port))
            print(size / (time.time() - start))
            sys.exit()

if __name__ == '__main__':
    send(sys.argv)
