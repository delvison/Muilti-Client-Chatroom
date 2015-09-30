from tkinter import *
from chat_gui import *
from datetime import datetime
import socket
import os
import sys
import select

RECV_BUFR = 4096 # receive buffer size
USERS_CONNECTED = [] # users who exist in the chatroom
SOCKET = [] # socket to the server
USERNAME = [] # users username
DEBUG = True # debug flag

def connect_to_server(gui,SERVER_IP,SERVER_PORT,username):
    """
    Attempts to connect to the server using the given username.
    """
    try:
        clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        clientsocket.connect((SERVER_IP, SERVER_PORT))
        clientsocket.send(bytes(username,'UTF-8'))
        clientsocket.settimeout(30)
        ack = clientsocket.recv(RECV_BUFR).decode()

        if ack != "NOT_UNIQUE":
            SOCKET.append(clientsocket)
            return [1,clientsocket]
        else:
            print("Username already exist.")
            return [0,clientsocket]
    # chat server offline
    except(ConnectionRefusedError):
        print("Server offline")
        gui.chat.insert(END,"Server offline.\n")
        return -1

def run_client(gui):

    try:
        # socket_list = [sys.stdin, SOCKET[0]]
        socket_list = [gui.SOCKET]

        # Get the list sockets which are readable
        # read_sockets, write_sockets, error_sockets = \
        # select.select(socket_list , [], [],)

        # for sock in read_sockets:
        #     # incoming message from remote server
        #     if sock == gui.SOCKET:
        #         recv_msg(gui,sock)
        #         print("recieve")
        #
        #     # user entered a message
        #     # else:
        #     #     send_msg(gui.SOCKET,sys.stdin.readline())

        # gui.after(1000,run_client(gui))

    except(KeyboardInterrupt):
        print("Program terminated.")
        sys.exit()

    except:
        gui.chat.insert(END,"\nDisconnected.\n")
        sys.exit()

def recv_msg(gui,socket):
    """
    Allows the program to recieve a message on the given socket.
    """
    data = socket.recv(RECV_BUFR)
    if not data :
        sys.exit()
    else:
        # print newly received message
        data = data.decode()
        gui.chat.insert(END,"\n"+data)

        # a new user has entered
        if "[*]" in data and "entered" in data and len(data.strip()) >= 1:
            gui.add_user(data.split(" ")[-2])

        # a user has left
        if "[*]" in data and "exited" in data:
            gui.remove_user(data.split(" ")[-2])

def socket_handler(gui,socket):
    try:
        while 1:
            # socket_list = [sys.stdin, SOCKET[0]]
            socket_list = [socket]

            # Get the list sockets which are readable
            read_sockets, write_sockets, error_sockets = \
            select.select(socket_list , [], [],)

            for sock in read_sockets:
                # incoming message from remote server
                if sock == socket:
                    recv_msg(gui,sock)

                # user entered a message
                # else:
                #     send_msg(gui.SOCKET,sys.stdin.readline())

    except(KeyboardInterrupt):
        print("Program terminated.")
        sys.exit()

    except:
        gui.chat.insert(END,"\nDisconnected.\n")

def send_msg(server_socket,msg):
    """
    Allows a user to send a message to the chat server using the given socket.
    """
    server_socket.send(bytes(msg,'UTF-8'))


if __name__ == "__main__":
    # initialize the GUI
    root = Tk()
    gui_root = chat_gui(master=root)
    gui_root.mainloop()

