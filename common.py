import socket
import json
import time
import sys
import random

def send_msg(receiver_addr, msg, msg_loss):
    # emulate message loss
    if random.random() < msg_loss:
        return
    try:
        msg = json.dumps(msg)
        send_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        send_socket.connect(receiver_addr)
        send_socket.sendall(msg.encode('utf-8'))
        send_socket.close()
    except Exception as e:
        return


def broadcast_msg(replica_list, msg, msg_loss):
    for receiver_addr in replica_list:
        send_msg(receiver_addr, msg, msg_loss)





