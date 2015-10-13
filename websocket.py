
# import asyncore
# import socket

import re
import struct
import time
from hashlib import *
from base64 import *
import random

TEXT = 0x01
BINARY = 0x02

def sha1_handshake_key(key):
    # decoded = base64.b64decode(key_rcvd+"258EAFA5-E914-47DA-95CA-C5AB0DC85B11")
    # sha = hashlib.sha1()
    # sha.update(decoded)
    # new_key = base64.b64encode(sha.digest())
    # return new_key.decode(encoding = 'UTF-8')
    GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
    return b64encode(sha1((key + GUID).encode()).digest()).decode()


def websock_handshake (client, data):
    """
    Performs a standard websocket handshake.
    """
    # print('Handshaking===============')
    # print(data)
    # data = client.recv(1024)
    # headers = parse_headers(data)
    # key = headers['Sec-WebSocket-Key']
    key = (re.search('Sec-WebSocket-Key:\s+(.*?)[\n\r]+', data).groups()[0].strip())
    # print("#########HERE##############")
    shake = "HTTP/1.1 101 Switching Protocols\r\n"
    shake += "Upgrade: websocket\r\n"
    shake += "Connection: Upgrade\r\n"
    shake += "Sec-WebSocket-Accept: %s \r\n\r\n" % sha1_handshake_key(key)
    # print("SENDING SHAKE...")
    # print(shake)
    return client.send(bytes(shake,'UTF-8'))


def parse_headers (data):
    """
    Parses headers from http websocket handshake
    """
    headers = {}
    lines = data.splitlines()
    for l in lines:
            parts = l.split(": ", 1)
            if len(parts) == 2:
                    headers[parts[0]] = parts[1]
    headers['code'] = lines[len(lines) - 1]
    return headers

def parse_frame(buf):
    """
    Parse a WebSocket frame. If there is not a complete frame in the
    buffer, return without modifying the buffer.
    """
    payload_start = 2

    # try to pull first two bytes
    if len(buf) < 3:
        return [False,""]
    b = buf[0]
    fin = b & 0x80      # 1st bit
    # next 3 bits reserved
    opcode = b & 0x0f   # low 4 bits
    b2 = buf[1]
    mask = b2 & 0x80    # high bit of the second byte
    length = b2 & 0x7f    # low 7 bits of the second byte

    # check that enough bytes remain
    if len(buf) < payload_start + 4:
        return [False,""]
    elif length == 126:
        length, = struct.unpack(">H", buf[2:4])
        payload_start += 2
    elif length == 127:
        length, = struct.unpack(">I", buf[2:6])
        payload_start += 4

    if mask:
        mask_bytes = [b for b in buf[payload_start:payload_start + 4]]
        payload_start += 4

    # is there a complete frame in the buffer?
    if len(buf) < payload_start + length:
        return [False,""]

    # remove leading bytes, decode if necessary, dispatch
    payload = buf[payload_start:payload_start + length]
    buffer = buf[payload_start + length:]

    # use xor and mask bytes to unmask data
    if mask:
        unmasked = [mask_bytes[i % 4] ^ b
                        for b, i in zip(payload, range(len(payload)))]
        payload = "".join([chr(c) for c in unmasked])

    # s = payload.decode("UTF8")
    return [True,payload]

def encrypt_frame(s):
    """
    Encode and send a WebSocket message
    """

    message = ""
    # always send an entire message as one frame (fin)
    b1 = 0x81

    # opcode
    if False:
        b1 |= TEXT
        payload = s.encode("UTF8")
    elif type(s) == str:
        b1 |= BINARY
        payload = s

    message += chr(b1)

    # never mask frames from the server to the client
    b2 = 0
    length = len(payload)
    if length < 126:
        b2 |= length
        message += chr(b2)
    elif length < (2 ** 16) - 1:
        b2 |= 126
        message += chr(b2)
        l = struct.pack(">H", length)
        message += l
    else:
        l = struct.pack(">Q", length)
        b2 |= 127
        message += chr(b2)
        message += l

    message += payload

    # return str(message)
    return message

def length(self):
    return self.frame_length

def encodeMessage(buf, key):
    """ Apply a mask to some message data."""
    encoded_msg = bytearray()
    buf_len = len(buf)
    for i in range(buf_len):
        c = buf[i] ^ key[i % 4]
        encoded_msg.append(c)
    return encoded_msg

def buildMessage(buf, mask=False):
    """
    Build a data frame from scratch.
    """
    buf = buf.encode("utf-8")
    msg = bytearray()

    # Generate a mask key: 32 random bits.
    if mask:
        key = [(random.randrange(1, 255)) for i in range(4)]

    # Build the first byte of header.
    ##
    # The first byte indicates that this is the final data frame
    # opcode is set to 0x1 to indicate a text payload.
    msg.append(0x81)  # 1 0 0 0 0 0 0 1

    # Build rest of the header and insert a payload.
    ##
    # How we build remaining header depends on buf size.
    buf_len = len(buf)

    if buf_len < 126:
        msg_header = buf_len  # prepare the payload size field

        if mask:
            # set the mask flag to 1
            msg.append(msg_header + (1 << 7))
        else:
            msg.append(msg_header)

        # Apply a mask and insert the payload.
        if mask:
            msg.append(key)  # insert the mask key as a header field
            msg.append(Frame.encodeMessage(buf, key))
        else:
            msg += bytearray(buf)
        return msg

    # If the buffer size is greater than can be described by 7 bits but
    # will fit into 16 bits use an extended payload size of 16 bits
    if buf_len <= ((1 << 16) - 1):

        if mask:
            # Make the payload field (7 bits 126) and set the mask flag
            msg.append(126 + (1 << 7))
        else:
            # No need to set the mask flag.
            msg.append(126)

        # Convert the buffer size into a 16 bit integer
        for i in range(1, 3):
            msg_header = (buf_len >> (16 - (8*i))) & (2**8 - 1)
            msg.append(msg_header)

        # Insert the payload and apply a mask key if necessary
        if mask:
            msg.append(key)
            msg.append(Frame.encodeMessage(buf, key))
        else:
            msg += buf
        return msg

    # If the buffer length can only be described by something larger than
    # a 16 bit int, extended payload will be 64 bits.
    if buf_len <= ((1 << 64) - 1):

        # Same as previous except with a payload field indicating 64 bit
        # extended playload header.
        if mask:
            msg.append(127 + (1 << 7))
        else:
            msg.append(127)

        for i in range(1, 9):
            # Make the buffer size a 64 bit int.
            msg_header = (buf_len >> (64 - (8*i))) & (2**8 - 1)
            msg.append(msg_header)

        # Prepare/insert the payload.
        if mask:
            msg.append(key)
            msg.append(Frame.encodeMessage(buf, key))
        else:
            msg += bytearray(buf)
        return msg

