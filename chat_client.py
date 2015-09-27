import socket
import os

SERVER_IP = '10.12.26.110'
SERVER_PORT = 3001
RECV_BUFR = 4096
USERS_CONNECT = []
SOCKET = ''

def chat_client():
    # ask for ip to connect to
    # SERVER_IP = input("server_ip > ")
    # ask for port number
    # SERVER_PORT = input("server_port > ")
    # ask for username
    username = input("username > ")

    # attempt to connect
    if connect_to_server(username) == 1:
        while 1:
            print("connected")
            # TODO: fix me


def connect_to_server(username):
    try:
        clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        clientsocket.connect((SERVER_IP, SERVER_PORT))
        clientsocket.send(bytes(username,'UTF-8'))
        ack = clientsocket.recv(RECV_BUFR).decode()

        if ack != "NOT_UNIQUE":
            SOCKET = clientsocket
            return 1
        else:
            return 0
    # chat server offline
    except(ConnectionRefusedError):
        print("Server offline")
        return -1


if __name__ == "__main__":
    chat_client()
