import socket

serverSocket = socket.socket()

# Bind and listen
serverSocket.bind(("127.0.0.1", 9090))
serverSocket.listen()


def f(arg):
    return str(eval(arg)/2)


while True:
    (clientConnected, clientAddress) = serverSocket.accept()
    print("Accepted a connection request from %s:%s" % (clientAddress[0], clientAddress[1]))

    dataFromClient = clientConnected.recv(1024)

    # Send some data back to the client
    clientConnected.send(f(dataFromClient.decode()).encode())

    clientConnected.close()

    # Breaking once connection closed
    break
