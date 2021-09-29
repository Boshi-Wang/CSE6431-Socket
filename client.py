

import socket

clientSocket = socket.socket()

# Connect to the server
clientSocket.connect(("127.0.0.1", 9090))

# Send data to server
data = "50"
clientSocket.send(data.encode())

# Receive data from server
dataFromServer = clientSocket.recv(1024)

# Print to the console
print(dataFromServer.decode())
