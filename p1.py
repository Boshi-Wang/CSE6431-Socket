from process import Process
import time

all_ports = [10000, 20000, 30000]

# init and start sub-threads
p = Process(pid=1, all_ports=all_ports, num_processes=len(all_ports), request_ts_l=[[], [63, 200], [4]])
time.sleep(5)   # wait for staring other processes
p.start_CS_thread()
p.start_listen_thread()


p.send_request(target_pid_list=[0, 2], job_config=[4,   'WithdrawCash', 'C', 30])
p.send_request(target_pid_list=[0, 2], job_config=[63,  'DepositCash',  'B', 40])
p.send_request(target_pid_list=[0, 2], job_config=[200, 'CheckBalance', 'B', None])

