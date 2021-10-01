# Implementing Lamport's algorithm for distributed mutual exclusion
- run ```python init_database.py``` to init the data
- run ```python p0.py``` and ```python p1.py```, each would start a process

- an example failure case is in below. It's not the code's bug but rather the bug of this setting.

p0: 4, 10; p1: 2, 5

what if p0 sends the second request when p1 hasn't sent the second request?