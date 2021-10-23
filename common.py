import socket
import json
import time
import sys

def send_msg(receiver_addr, msg):
    send_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    send_socket.connect(receiver_addr)
    send_socket.sendall(msg.encode('utf-8'))
    send_socket.close()


def broadcast_msg(msg, replica_list):
    for receiver_addr in replica_list:
        send_msg(receiver_addr, json.dumps(msg))





