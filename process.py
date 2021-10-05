import socket
import threading
from database_utils import execute_op

REQUEST = 0
REPLY = 1

id2user = {0: 'A', 1: 'B', 2: 'C'}
user2id = {'A': 0, 'B': 1, 'C': 2}


class Process:
    def __init__(self, pid, all_ports, num_processes, request_ts_l):
        assert num_processes == len(all_ports)

        self.pid = pid                # integer from 0 to NUM_PROC-1, indicating unique id of this process
        self.all_ports = all_ports    # list of ports for each process
        self.port = all_ports[pid]    # this process' own port
        self.num_processes = num_processes
        self.d = 1                    # the bump up for lamport's logical lock
        self.request_ts_l = request_ts_l  # list of request timestamps to be sent out in the future

        # initialize a server
        self.serverSocket = socket.socket()
        self.serverSocket.bind(("127.0.0.1", self.port))  # all process communicate with 127.0.0.1, with different ports
        self.serverSocket.listen()

        self.listen_thread = None     # a bunch of threads used for listening to incoming messages
        self.in_CS_l = [False, False, False]   # whether in critical section for each user
        self.deferred_list_l = [[], [], []]       # list of pids with deferred reply
        self.request_timestamp_l = [None, None, None]  # the timestamp of the current sent pending request; None if no
        self.job_to_exec_l = [None, None, None]        # The job to execute in CS. None if no.
        self.reply_received_l = [[], [], []]       # list of process ids where reply is received

        self.CS_thread_l = [None, None, None]          # a thread which detects whether can enter CS for each user

        self.do_CS = False
        self.do_listen = False

    def exec_job(self, userid):
        job_to_exec = self.job_to_exec_l[userid]
        execute_op(job_to_exec)

    def start_listen_thread(self):
        def listen_exec_func(self):
            while self.do_listen:
                (clientConnected, clientAddress) = self.serverSocket.accept()
                received_data = clientConnected.recv(1024).decode().split()
                messager_pid, message_timestamp, message_type, userid = \
                    int(received_data[0]), int(received_data[1]), int(received_data[2]), int(received_data[3])
                assert message_type in [REQUEST, REPLY]
                if message_type == REPLY:
                    self.reply_received_l[userid].append(messager_pid)
                    print("received reply from p{} ".format(messager_pid))
                else:
                    # received a REQUEST
                    print("received request from p{} with timestamp {} ".format(messager_pid, message_timestamp))
                    # send back a reply if necessary
                    do_reply = True
                    if self.in_CS_l[userid]:
                        # no reply if no critical section
                        do_reply = False
                    elif not(self.request_timestamp_l[userid] is None) and self.request_timestamp_l[userid] < message_timestamp:
                        # no reply if current pending request has smaller timestamp
                        do_reply = False
                    elif len(self.request_ts_l[userid]) > 0:
                        # no reply if there exists future requests yet to make with smaller timestamp
                        if self.request_ts_l[userid][0] < message_timestamp:
                            do_reply = False

                    print("do_reply:", do_reply)
                    print("\t reason: in_CS:{}, req_timestamp:{}, req_ts:{} ".format(
                                self.in_CS_l[userid], self.request_timestamp_l[userid], self.request_ts_l[userid]))
                    if do_reply:
                        self.send_reply(messager_pid, userid)
                    else:
                        self.deferred_list_l[userid].append([messager_pid, message_timestamp])

        # initialize and start the listening threads
        self.do_listen = True
        self.listen_thread = threading.Thread(target=listen_exec_func, args=(self,))
        print("Start listen_thread...")
        self.listen_thread.start()


    def start_CS_thread(self):
        """
        start a thread for each user which constantly check if ok to enter Critical Section (CS).
        If yes then enter & leave CS.
        """
        def CS_exec_func(self, userid):
            while self.do_CS:
                # wait until there's a job to execute
                while (self.job_to_exec_l[userid] is None) and self.do_CS:
                    pass
                # see if can access CS
                if set(self.reply_received_l[userid]) == set(range(self.num_processes))-{self.pid}:
                    self.in_CS_l[userid] = True
                    print("BEGIN <CS> ")
                    # perform self.job_to_execute
                    self.exec_job(userid)
                    print("END <CS> ")
                    self.reply_received_l[userid] = []  # empty the list
                    # send a reply to all deferred requests
                    for [deferred_pid, message_timestamp] in self.deferred_list_l[userid]:
                        if len(self.request_ts_l[userid]) == 0:
                            self.send_reply(deferred_pid, userid)
                        elif self.request_ts_l[userid][0] > message_timestamp:
                            self.send_reply(deferred_pid, userid)

                    self.in_CS_l[userid] = False
                    self.job_to_exec_l[userid] = None
                    self.request_timestamp_l[userid] = None

        print("Start CS_thread")
        self.do_CS = True
        for userid in [0, 1, 2]:
            self.CS_thread_l[userid] = threading.Thread(target=CS_exec_func, args=(self, userid))
        for userid in [0, 1, 2]:
            self.CS_thread_l[userid].start()

    def send_request(self, target_pid_list, job_config):
        """
        send a request to processes listed in target_pid_list.
        job_config: [timestamp, action, user, amount]
        """
        timestamp, action, user, amount = job_config
        assert action in ['DepositCash', 'WithdrawCash', 'ApplyInterest', 'CheckBalance']
        assert user in ['A', 'B', 'C']
        if amount is None:
            assert action == 'CheckBalance'

        userid = user2id[user]
        # wait until currently there's no current pending request
        while not (self.request_timestamp_l[userid] is None):
            pass

        self.job_to_exec_l[userid] = [action, user, amount]

        self.request_timestamp_l[userid] = timestamp
        for target_pid in target_pid_list:
            # send data to target server
            clientSocket = socket.socket()
            clientSocket.connect(("127.0.0.1", self.all_ports[target_pid]))
            clientSocket.send("{} {} {} {}".format(self.pid, self.request_timestamp_l[userid], REQUEST, userid).encode())
            clientSocket.close()
            print("sent request to p{} with timestamp {} ".format(target_pid, self.request_timestamp_l[userid]))
        del self.request_ts_l[userid][0]   # delete the sent request

    def send_reply(self, target_pid, userid):
        clientSocket = socket.socket()
        clientSocket.connect(("127.0.0.1", self.all_ports[target_pid]))
        # send data to target server
        clientSocket.send("{} {} {} {}".format(self.pid, -1, REPLY, userid).encode())  # timestamp is -1 as it's not used
        print("sent reply to p{}".format(target_pid))
        clientSocket.close()

    def end(self):
        self.do_listen, self.do_CS = False, False
        self.listen_thread.join()
        for userid in [0, 1, 2]:
            self.CS_thread_l[userid].join()
        return

