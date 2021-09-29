from process import Process
import time

all_ports = [10000, 20000]

# init and start sub-threads
p1 = Process(pid=1, all_ports=all_ports, num_processes=len(all_ports), d=1)
p1.simple_event()

time.sleep(5)   # wait for staring other processes
p1.start_CS_thread()
p1.start_listen_thread()

# now wants to enter the critical section
p1.send_request(0)


