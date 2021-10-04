from process import Process
import time

all_ports = [10000, 20000, 30000]

# init and start sub-threads
p = Process(pid=0, all_ports=all_ports, num_processes=len(all_ports), request_ts_l=[[4, 200], [], [57]])
time.sleep(5)   # wait for staring other processes
p.start_CS_thread()
p.start_listen_thread()


p.send_request(target_pid_list=[1, 2], job_config=[4,   'DepositCash',   'A', 20])
p.send_request(target_pid_list=[1, 2], job_config=[57,  'ApplyInterest', 'C', 0.1])
p.send_request(target_pid_list=[1, 2], job_config=[200, 'CheckBalance',  'A', None])

