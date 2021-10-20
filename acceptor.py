"""Acceptor Implementation in MultiPaxos"""
import socket
import json
import time
import threading
import sys

class Acceptor:
    def __init__(self, replica):
        self.f = replica.f
        self.replicaList = replica.replicaList
        self.replicaID = replica.replicaID
        self.view = replica.view
        self.addr = replica.addr
        

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
            return True
        return False

        