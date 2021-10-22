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

        self.pa_sequence = replica.pa_sequence
        self.client_record = replica.client_record

    def change_leader(self, msg):
        # modular?
        if self.view[0] <= msg['replicaID']:
            print("# Acceptor {} accepts {} as new leader".format(self.replicaID, msg['replicaID']))
            sys.stdout.flush()
            self.view[0] = msg['replicaID']
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
    def send_msg(self, receiver_addr, msg):
        send_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        send_socket.connect(receiver_addr)
        send_socket.sendall(msg.encode('utf-8'))
        send_socket.close()

    def process_proposal(self, msg):
        view = msg['view']
        if view < self.view[0]:
            return
        elif view > self.view[0]:
            self.view[0] = view
        seq_num = msg['seq_num']
        while seq_num >= len(self.pa_sequence):
            self.pa_sequence.append({})

        self.pa_sequence[seq_num] = {
                'client': msg['client'],
                'message': msg['message'],
                'view': msg['view']
        }
        new_msg = {}
        new_msg['type'] = 'Accept'
        new_msg['replicaID'] = self.replicaID
        new_msg['message'] = msg['message']
        new_msg['client'] = msg['client']
        new_msg['view'] = msg['view']
        new_msg['seq_num'] = msg['seq_num']
        for receiver_addr in self.replicaList:
            self.send_msg(receiver_addr, json.dumps(new_msg))
        