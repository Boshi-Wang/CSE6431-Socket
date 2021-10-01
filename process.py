import socket
import threading
import time
import json

REQUEST = 0
REPLY = 1


class Process:
    def __init__(self, pid, all_ports, num_processes):
        assert num_processes == len(all_ports)

        self.pid = pid                # integer from 0 to NUM_PROC-1, indicating unique id of this process
        self.all_ports = all_ports    # list of ports for each process
        self.port = all_ports[pid]    # this process' own port
        self.num_processes = num_processes
        self.local_lock = 0           # local logical timestamp
        self.d = 1                    # the bump up for lamport's logical lock
        self.events = []              # record past event

        # initialize a server
        self.serverSocket = socket.socket()
        self.serverSocket.bind(("127.0.0.1", self.port))  # all process communicate with 127.0.0.1, with different ports
        self.serverSocket.listen()

        self.listen_thread = None
        self.do_listen = False
        self.in_CS = False
        self.deferred_list = []  # list of pids with deferred reply
        self.request_timestamp = None  # None if not currently making any request (either no request or in CS)
        self.job_to_exec = None        # None if not currently making request. Stores the job to execute in CS.
        self.reply_received = []  # list which records the pids where reply is received

        self.CS_thread = None
        self.do_CS = False

    def exec_job(self):
        with open('data.json', 'r') as fp:
            data = json.load(fp)
        [action, user, amount] = self.job_to_exec
        if action == 'DepositCash':
            old_ = data[user]
            data[user] = data[user] + amount
            print("DepositCash to User {}, amount:{}->{} ".format(user, old_, data[user]))
        elif action == 'WithdrawCash':
            old_ = data[user]
            data[user] = data[user] - amount
            print("WithdrawCash to User {}, amount:{}->{} ".format(user, old_, data[user]))
        elif action == 'ApplyInterest':
            old_ = data[user]
            data[user] = data[user] * (1 + amount)
            print("ApplyInterest to User {}, amount:{}->{} ".format(user, old_, data[user]))
        elif action == 'CheckBalance':
            print("CheckBalance to User {}, amount:{}".format(user, data[user]))
        else:
            assert False
        with open('data.json', 'w') as fp:
            json.dump(data, fp)

    def start_listen_thread(self):
        # start a thread which would repeated listen for any message sent to this port
        def listen_exec_func(self):
            while self.do_listen:
                (clientConnected, clientAddress) = self.serverSocket.accept()
                received_data = clientConnected.recv(1024).decode().split()
                messager_pid, message_timestamp, message_type = int(received_data[0]), int(received_data[1]), int(received_data[2])
                assert message_type in [REQUEST, REPLY]
                if message_type == REPLY:
                    self.reply_received.append(messager_pid)
                    print("received reply from process {} ".format(messager_pid))
                    self.events.append((self.local_lock,
                                        "received reply from process {} ".format(messager_pid)))
                else:
                    # update local lock and event record
                    # TODO: do we update here as below? I think not
                    # self.local_lock = max(self.local_lock, message_timestamp) + self.d
                    print("received request from process {} with timestamp {} ".format(messager_pid, message_timestamp))
                    self.events.append((self.local_lock,
                        "received request from process {} with timestamp {} ".format(messager_pid, message_timestamp)))

                    # send back a reply if necessary
                    do_reply = True
                    if self.in_CS:
                        do_reply = False
                    else:
                        if not(self.request_timestamp is None) and self.request_timestamp < message_timestamp:
                            do_reply = False
                    print("do_reply:", do_reply)
                    print("\t reason: in_CS:{}, req_timestamp:{}, local_lock:{} ".format(self.in_CS, self.request_timestamp, self.local_lock))
                    if do_reply:
                        # clientConnected.send("{} {} {}".format(self.pid, self.local_lock, REPLY).encode())
                        self.send_reply(messager_pid)
                    else:
                        self.deferred_list.append(messager_pid)

        self.listen_thread = threading.Thread(target=listen_exec_func, args=(self,))
        self.do_listen = True
        print("Start listen_thread...")
        self.listen_thread.start()

    def start_CS_thread(self):
        # start a thread which constantly check if ok to enter Critical Section (CS). If yes then enter/leave CS.
        def CS_exec_func(self):
            while self.do_CS:
                # see if can access CS
                if set(self.reply_received) == set(range(self.num_processes))-{self.pid}:
                    self.in_CS = True
                    print("BEGIN <CS> ")
                    # perform job_to_execute
                    assert not(self.job_to_exec is None)
                    self.exec_job()
                    print("END <CS> ")
                    self.reply_received = []  # empty the list
                    # send a reply to all deferred requests
                    for deferred_pid in self.deferred_list:
                        self.send_reply(deferred_pid)
                    self.in_CS = False
                    self.job_to_exec = None
                    self.request_timestamp = None

        self.CS_thread = threading.Thread(target=CS_exec_func, args=(self,))
        print("Start CS_thread")
        self.do_CS = True
        self.CS_thread.start()

    def send_request(self, target_pid, job_config):
        # wait until currently there's no request
        while not (self.request_timestamp is None):
            pass
        timestamp, action, user, amount = job_config
        timestamp = int(timestamp)
        assert action in ['DepositCash', 'WithdrawCash', 'ApplyInterest', 'CheckBalance']
        assert user in ['A', 'B', 'C']
        if amount is None:
            assert action == 'CheckBalance'
        self.job_to_exec = [action, user, amount]

        clientSocket = socket.socket()
        self.local_lock = timestamp
        self.request_timestamp = self.local_lock
        clientSocket.connect(("127.0.0.1", self.all_ports[target_pid]))
        # send data to target server
        clientSocket.send("{} {} {}".format(self.pid, self.request_timestamp, REQUEST).encode())
        clientSocket.close()
        print("sent request to process {} with timestamp {} ".format(target_pid, self.request_timestamp))
        self.events.append((self.local_lock, "sent request to process {} with timestamp {} ".format(target_pid, self.request_timestamp)))

    def send_reply(self, target_pid):
        clientSocket = socket.socket()
        clientSocket.connect(("127.0.0.1", self.all_ports[target_pid]))
        # send data to target server
        clientSocket.send("{} {} {} ".format(self.pid, self.local_lock, REPLY).encode())
        print("sent reply to process {}".format(target_pid))
        self.events.append((self.local_lock, "sent reply to process {} ".format(target_pid)))
        clientSocket.close()

    def print_events(self):
        print(self.events)

    def end(self):
        self.do_listen, self.do_CS = False, False
        self.listen_thread.join()
        self.CS_thread.join()
        return

