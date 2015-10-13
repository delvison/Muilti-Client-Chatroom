# file: chat_server.py

from datetime import datetime
import sys
import socket
import select
from websocket import *

HOST = socket.gethostbyname(socket.gethostname())
SOCKET_LIST = {} # dictionary of sockets and users = {username:socket,...}
WEBSOCKET_USERS = [] # holds IPs of connections that are websockets
RECV_BUFR = 4096 # buffer size for messages
# PORT = 3001 # port of server being connected to
PORT = 3001 # port of server being connected to
LINE = "\n##################################################################\n"
STAR = "[*] " # event marker -- tells when a person enters or leaves room
DEBUG = False # debugger flag
COMMANDS = ["HELP","KICK","LIST_USERS","EXIT"]

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

    print((LINE+"Chat running " +str(HOST)+":"+ str(PORT)+LINE))
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
                    m = sys.stdin.readline().rstrip()
                    # check if the user is inputting a command
                    if m.split(" ")[0] in COMMANDS \
                    and len(m.split(" ")) <= 2:
                        process_command(m)
                    else:
                        send_msg_to_all(server_socket,server_socket,"server",
                        "server: "+m)

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


def recv_msg(server_socket, sock, websocket_msg=None):
    """
    Recieves a message from the given socket.
    """
    # receive message
    if websocket_msg is None:
        data = None
    else:
        data = websocket_msg
    try:
        if data is None:
            data = sock.recv(RECV_BUFR)
            data = data.decode()
        username = get_username(sock)
        if data is not None:
            msg = username+" > "+data.rstrip()
            print(("\n"+"["+datetime.now().strftime('%H:%M:%S')+"] "+msg))
            send_msg_to_all(server_socket, sock, username, msg)

        # remove broken socket
        else:
            remove_user(username)

    # websocket connection
    except(UnicodeDecodeError):
        is_valid, decoded = parse_frame(data)
        if is_valid:
            recv_msg(server_socket,sock,decoded)
        else:
            print("INVALID")

    except(UnboundLocalError):
        print("ERROR: Attempted to send to user that doesnt exist.")

    except(ConnectionResetError):
        print("ERROR: Unexpectedly disconnected.")

    except(NameError):
        msg = STAR+username+" exited."
        print(("\n"+msg))
        send_msg_to_all(server_socket, sock, username, msg)



def send_msg_to_all(server_socket, senders_socket,senders_username, message):
    """
    Sends a message to all other connected clients.
    """
    debug("Entering send_msg_to_all")
    for username, socket in list(SOCKET_LIST.items()):
        if socket != server_socket and socket != senders_socket:
            # try:
                # attempt to send message to client
                message = "["+datetime.now().strftime('%H:%M:%S')+"] "+message
                if username not in WEBSOCKET_USERS:
                    print("not a websocket")
                    socket.send(bytes(message,'UTF-8'))
                else:
                    print("is a websocket")
                    c = encrypt_frame(message)
                    b = buildMessage(message)
                    # socket.send("\x00"+b+"\xFF")
                    print(b)
                    print(c)
                    socket.send(b)
            # except Exception as e:
            #     print(e)
            #     # close socket if message fails
            #     socket.close()
            #     # remove client from the sockets list
            #     remove_user(username)
    prompt()


def add_user(server_socket):
    """
    Adds a user to the chat room.
    """
    username = '' #placeholder for username
    is_websocket = False

    # Accept new connections into chat
    new_sock, new_addr = server_socket.accept()

    # receive newly connected client's username
    first_msg = new_sock.recv(RECV_BUFR)


    if (len(first_msg.decode().rstrip())< 20):
        username = first_msg.decode().rstrip()
    else:
        websock_handshake(new_sock,first_msg.decode(encoding='UTF-8'))
        username = new_sock.recv(RECV_BUFR)
        is_valid,username = parse_frame(username)
        is_websocket = True


    # print(username);
    # new_sock.settimeout(30)
    if username not in SOCKET_LIST and username.strip() != "":
        SOCKET_LIST[username] = new_sock
        # send ACK
        new_sock.send(bytes("OK",'UTF-8'))
        # inform new user of current users in the chat
        all_users = ''
        for user,socket in list(SOCKET_LIST.items()):
            all_users += "&"+user
        new_sock.send(bytes(all_users,'UTF-8'))
        # inform all users that a new user has entered
        mesg = STAR+username+ " entered."
        print(("\n"+mesg))
        print_all_users()
        send_msg_to_all(server_socket,new_sock,username,mesg)
        if is_websocket:
            WEBSOCKET_USERS.append(username)
    else:
        # send message informing that the username is not unique
        print((username+" "+str(new_addr)+" failed to connect."))
        new_sock.send(bytes("NOT_UNIQUE",'UTF-8'))
        new_sock.close()
        prompt()

def remove_user(username):
    """
    Takes in an open socket, closes the socket which essentially removes a
    user, and informs the other users that the user has been removed.
    """
    # remove socket from sockets list
    try:
        # close socket
        SOCKET_LIST[username].close()
        del SOCKET_LIST[username]
        # inform the chat room
        msg = STAR+username + " exited."
        print(msg)
        print_all_users()
        send_msg_to_all(SOCKET_LIST['server'],SOCKET_LIST['server'] ,\
        'server', msg)
    except KeyError:
        pass


def get_username(socket):
    """
    Receives a socket and returns the username associated with that socket.
    """
    u = ''
    for username, sock in list(SOCKET_LIST.items()):
        if socket == sock:
            u = username
    return u

def get_all_sockets():
    """
    Returns list of all sockets connected.
    """
    all_sockets = []
    all_sockets.append(sys.stdin)
    for username, socket in list(SOCKET_LIST.items()):
        all_sockets.append(socket)
    return all_sockets

def print_all_users():
    all_users = "\nUSERS: ["
    for user, socket in list(SOCKET_LIST.items()):
        all_users+= user+","
    print((all_users[:-1]+"]"))

def process_command(cmd):
    try:
        # HELP
        if cmd.split(" ")[0] == COMMANDS[0]:
            print("Commands: ")
            for c in COMMANDS:
                print(("   "+c))
            prompt()
        # KICK [USER]
        if cmd.split(" ")[0] == COMMANDS[1]:
            remove_user(cmd.split(" ")[1])
        # LIST_USERS
        if cmd.split(" ")[0] == COMMANDS[2]:
            print_all_users()
            prompt()
        # EXIT
        if cmd.split(" ")[0] == COMMANDS[3]:
            sys.exit()
    except IndexError:
        pass

def debug(msg):
    if DEBUG:
        print(msg)



if __name__ == "__main__":
    chat_server()







# from websocket import create_connection
# ws = create_connection("ws://localhost:8080/websocket")
# print "Sending 'Hello, World'..."
# ws.send("Hello, World")
# print "Sent"
# print "Reeiving..."
# result =  ws.recv()
# print "Received '%s'" % result
# ws.close()
