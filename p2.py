from process import Process
import time

all_ports = [10000, 20000, 30000]

# init and start sub-threads
p = Process(pid=2, all_ports=all_ports, num_processes=len(all_ports), request_ts=[2, 68, 202])
time.sleep(5)   # wait for staring other processes
p.start_CS_thread()
p.start_listen_thread()


p.send_request(target_pid_list=[0, 1], job_config=[2,   'ApplyInterest', 'B', 0.1])
p.send_request(target_pid_list=[0, 1], job_config=[68,  'WithdrawCash',  'A', 10])
p.send_request(target_pid_list=[0, 1], job_config=[202, 'CheckBalance',  'C', None])

