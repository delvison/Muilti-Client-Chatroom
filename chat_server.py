# file: chat_server.py

import sys
import socket
import select

HOST = socket.gethostbyname(socket.gethostname())
SOCKET_LIST = {} # username:socket
RECV_BUFR = 4096
PORT = 3001
LINE = "\n##################################################################\n"
STAR = "[*] "
DEBUG = True

def chat_server():
    """
    Initiates the chat server.
    """
    # establish server socket to listen on the given port
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen(10)

    # add the server socket to the list of open sockets
    SOCKET_LIST['server'] = server_socket

    print(LINE+"Chat running " +str(HOST)+":"+ str(PORT)+LINE)

    while 1:
        all_sockets = get_all_sockets()
        ready_to_read,ready_to_write,in_error = \
        select.select(all_sockets,[],[],0)

        for sock in ready_to_read:
            # a new connection request is received
            if sock == server_socket:
                add_user(server_socket)

            # a message from a client is received
            else:
                recv_msg(server_socket,sock)


def recv_msg(server_socket, sock):
    """
    Recieves a message from the given socket.
    """
    # receive message
    try:
        data = sock.recv(RECV_BUFR).decode()
        username = get_username(sock)
        if data:
                msg = username+": "+data.rstrip()
                print(msg)
                send_msg_to_all(server_socket, sock, username, msg)

        # remove broken socket
        else:
            remove_user(username, sock)

    # except(UnboundLocalError):
    #     print("ERROR: Attempted to send to user that doesnt exist.")

    # except(ConnectionResetError):
    #     print("ERROR: Unexpectedly disconnected.")

    except(NameError):
        msg = STAR+username+" is offline."
        print(msg)
        send_msg_to_all(server_socket, sock, username, msg)



def send_msg_to_all(server_socket, senders_socket,senders_username, message):
    """
    Sends a message to all other connected clients.
    """
    debug("Entering send_msg_to_all")
    for username, socket in SOCKET_LIST.items():
        if socket != server_socket and socket != senders_socket:
            # try:
                # attempt to send message to client
                socket.send(bytes(message,'UTF-8'))
            # except:
            #     # close socket if message fails
            #     socket.close()
            #     # remove client from the sockets list
            #     remove_user(username, socket)


def add_user(server_socket):
    """
    Adds a user to the chat room.
    """
    # Accept new connections into chat
    new_sock, new_addr = server_socket.accept()
    # receive newly connected client's username
    username = new_sock.recv(RECV_BUFR).decode()
    new_sock.settimeout(30)
    if username not in SOCKET_LIST:
        SOCKET_LIST[username] = new_sock
        new_sock.send(bytes("OK",'UTF-8'))
        mesg = STAR+username+ " entered the chat."
        print(mesg)
        send_msg_to_all(server_socket,new_sock,username,mesg)
    else:
        # send message informing that the username is not unique
        print(username+" "+str(new_addr)+" failed to connect.")
        new_sock.send(bytes("NOT_UNIQUE",'UTF-8'))
        new_sock.close()


def remove_user(username, socket):
    """
    Takes in an open socket, closes the socket which essentially removes a
    user, and informs the other users that the user has been removed.
    """
    # close socket
    socket.close()
    # remove socket from sockets list
    try:
        del SOCKET_LIST[username]
    except KeyError:
        pass
    # inform the chat room
    msg = username + " removed."
    send_msg_to_all(NIL, NIL, NIL, msg)

def get_username(socket):
    """
    Receives a socket and returns the username associated with that socket.
    """
    u = ''
    for username, sock in SOCKET_LIST.items():
        if socket == sock:
            u = username
    return u

def get_all_sockets():
    """
    Returns list of all sockets connected.
    """
    all_sockets = []
    for username, socket in SOCKET_LIST.items():
        all_sockets.append(socket)
    return all_sockets

def get_all_users():
    """
    Returns list of all users connected.
    """
    all_users= []
    for username, socket in SOCKET_LIST.items():
        all_users.append(username)
    return all_users

def debug(msg):
    if DEBUG:
        print(msg)



if __name__ == "__main__":
    chat_server()

