from process import Process
import time

all_ports = [10000, 20000]

# init and start sub-threads
p0 = Process(pid=0, all_ports=all_ports, num_processes=len(all_ports))

time.sleep(5)   # wait for staring other processes
p0.start_CS_thread()
p0.start_listen_thread()

# now p0 wants to enter the critical section
p0.send_request(target_pid=1, job_config=[4, 'DepositCash', 'B', 20])
p0.send_request(target_pid=1, job_config=[10, 'ApplyInterest', 'B', 1.0])

