"""Acceptor Implementation in MultiPaxos"""
import socket
import json
import time
import threading
import sys

from replica import MAXIMUM_LOG_SIZE

class Acceptor:
    def __init__(self, replica):
        self.f = replica.f
        self.replicaList = replica.replicaList
        self.replicaID = replica.replicaID
        self.view = replica.view
        self.addr = replica.addr
        
        self.chatLog = [MAXIMUM_LOG_SIZE]

    def change_leader(self, msg):
        # modular?
        if self.view <= msg['replicaID']:
            print("# Acceptor {} accepts {} as new leader".format(self.replicaID, msg['replicaID']))
            sys.stdout.flush()
            self.view = msg['replicaID']
            send_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            send_socket.connect(tuple(msg['addr']))
            msg = {}
            msg['type'] = 'YouAreLeader'
            msg['replicaID'] = self.replicaID
            msg = json.dumps(msg)
            send_socket.sendall(msg.encode('utf-8'))
            send_socket.close()
            return True
        return False

    def read_chatLog(self):
        return self.chatLog

    def update_chatLog(self, newLog):
        self.chatLog = newLog

        