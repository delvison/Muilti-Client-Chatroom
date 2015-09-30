# file: chat_server.py

from datetime import datetime
import sys
import socket
import select

HOST = socket.gethostbyname(socket.gethostname())
SOCKET_LIST = {} # dictionary of sockets and users = {username:socket,...}
RECV_BUFR = 4096 # buffer size for messages
PORT = 3001 # port of server being connected to
LINE = "\n##################################################################\n"
STAR = "[*] " # event marker -- tells when a person enters or leaves room
DEBUG = False # debugger flag

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
    prompt()

    while 1:
        try:
            all_sockets = get_all_sockets()
            ready_to_read,ready_to_write,in_error = \
            select.select(all_sockets,[],[],0)

            for sock in ready_to_read:
                # a new connection request is received
                if sock == server_socket:
                    add_user(server_socket)

                # sending a message
                elif sock == sys.stdin:
                    send_msg_to_all(server_socket,server_socket,"server",
                    "server: "+sys.stdin.readline().rstrip())

                # a message from a client is received
                else:
                    recv_msg(server_socket,sock)
        except(KeyboardInterrupt):
            print("Program terminated.")
            sys.exit()

def prompt():
    """
    Prints out the chat prompt.
    """
    sys.stdout.write("["+datetime.now().strftime('%H:%M:%S')+"] "+"server > ")
    sys.stdout.flush()


def recv_msg(server_socket, sock):
    """
    Recieves a message from the given socket.
    """
    # receive message
    try:
        data = sock.recv(RECV_BUFR).decode()
        username = get_username(sock)
        if data:
            msg = username+" > "+data.rstrip()
            print("\n"+"["+datetime.now().strftime('%H:%M:%S')+"] "+msg)
            send_msg_to_all(server_socket, sock, username, msg)

        # remove broken socket
        else:
            remove_user(username, sock)


    except(UnboundLocalError):
        print("ERROR: Attempted to send to user that doesnt exist.")

    except(ConnectionResetError):
        print("ERROR: Unexpectedly disconnected.")

    except(NameError):
        msg = STAR+username+" exited."
        print("\n"+msg)
        send_msg_to_all(server_socket, sock, username, msg)



def send_msg_to_all(server_socket, senders_socket,senders_username, message):
    """
    Sends a message to all other connected clients.
    """
    debug("Entering send_msg_to_all")
    for username, socket in SOCKET_LIST.items():
        if socket != server_socket and socket != senders_socket:
            try:
                # attempt to send message to client
                message = "["+datetime.now().strftime('%H:%M:%S')+"] "+message
                socket.send(bytes(message,'UTF-8'))
            except:
                # close socket if message fails
                socket.close()
                # remove client from the sockets list
                remove_user(username, socket)
    prompt()


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
        # send ACK
        new_sock.send(bytes("OK",'UTF-8'))
        # inform new user of current users in the chat
        all_users = ''
        for user,socket in SOCKET_LIST.items():
            all_users += "&"+user
        new_sock.send(bytes(all_users,'UTF-8'))
        # inform all users that a new user has entered
        mesg = STAR+username+ " entered."
        print("\n"+mesg)
        print_all_users()
        send_msg_to_all(server_socket,new_sock,username,mesg)
    else:
        # send message informing that the username is not unique
        print(username+" "+str(new_addr)+" failed to connect.")
        new_sock.send(bytes("NOT_UNIQUE",'UTF-8'))
        new_sock.close()
        prompt()

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
    msg = username + " exited."
    print_all_users()
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
    all_sockets.append(sys.stdin)
    for username, socket in SOCKET_LIST.items():
        all_sockets.append(socket)
    return all_sockets

def print_all_users():
    all_users = "\nUSERS: ["
    for user, socket in SOCKET_LIST.items():
        all_users+= user+","
    print(all_users[:-1]+"]")

def debug(msg):
    if DEBUG:
        print(msg)



if __name__ == "__main__":
    chat_server()

