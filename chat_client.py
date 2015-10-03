#! /usr/bin/python3

"""
    This application is meant to be a chat client that connects to a central
    server. All messages are sent and received from the server. In order for the
    user to connect to the server, he or she must have a unique username that
    does not already exist on the server.

    Usage:
        python chat_client.py -c   -- cli mode
        python chat_client.py      -- gui mode

    @author Delvison Castillo (delvisoncastillo@gmail.com)
"""
from tkinter import *
from chat_gui import *
from chat_client_cli import *
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
    Attempts to connect to the server using the given username. Upon connection
    attempt, the server replies with an acknowledgement message that indicates
    whether or not the user name is unique.

    Returns a tuple containing a 0,1, or -1 in the first index followed by the
    socket in the second index.
    """
    try:
        # attempt to connect to server
        clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        clientsocket.connect((SERVER_IP, SERVER_PORT))

        # send username
        clientsocket.send(bytes(username,'UTF-8'))
        clientsocket.settimeout(30)
        ack = clientsocket.recv(RECV_BUFR).decode()

        if ack != "NOT_UNIQUE": # unique username
            SOCKET.append(clientsocket)
            return [1,clientsocket]
        else: # username is not unique
            return [0,clientsocket]

    # chat server offline
    except(ConnectionRefusedError):
        # gui.chat.insert(END,"\nServer offline.\n",fg='red')
        gui.display("\nServer offline.\n",color='red')
        return [-1,0]


def recv_msg(gui,socket):
    """
    Allows the program to recieve a message on the given socket. Takes in the
    GUI object and the active socket connected to the server. This function is
    also responsible for adding users into the chatroom in the GUI.
    """
    data = socket.recv(RECV_BUFR)
    if not data :
        sys.exit()
    else:
        # print newly received message
        data = data.decode()
        # gui.chat.insert(END,"\n"+data)
        gui.display("\n"+data)

        # a new user has entered. Add to the GUI
        if "[*]" in data and "entered" in data and len(data.strip()) >= 1:
            gui.add_user(data.split(" ")[-2])

        # a user has left. Remove from the GUI
        if "[*]" in data and "exited" in data:
            gui.remove_user(data.split(" ")[-2])


def socket_handler(gui,socket):
    """
    Handler for socket processing. Takes in the GUI object and the active socket
    that is connected to the chat server. This function runs on a thread that is
    seperate from the main thread since the main thread is occupied by the GUI's
    mainloop.
    """
    try:
        while 1:
            socket_list = [socket]

            # Get the list sockets which are readable
            read_sockets, write_sockets, error_sockets = \
            select.select(socket_list , [], [],)

            for sock in read_sockets:
                # incoming message from remote server
                if sock == socket:
                    recv_msg(gui,sock)

    except(KeyboardInterrupt):
        print("Program terminated.")
        sys.exit()

    except:
        # gui.chat.insert(END,"\nDisconnected.\n")
        gui.display("\nDisconnected.\n",color="red")


def send_msg(server_socket,msg):
    """
    Allows a user to send a message to the chat server using the given socket.
    """
    server_socket.send(bytes(msg,'UTF-8'))


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "-c":
        cli_chat_client()
    else:
        # initialize the GUI
        root = Tk()
        gui_root = chat_gui(master=root)
        gui_root.mainloop()

