"""Learner Implementation in MultiPaxos"""
import socket
import json
import time
import threading



class Learner:
    def __init__(self, replica):
        self.f = replica.f
        self.replicaList = replica.replicaList
        self.replicaID = replica.replicaID
        self.view = replica.view
        self.addr = replica.addr
        self.client_record = replica.client_record
        self.elected = replica.elected

        self.accept_record = {}
        self.learner_sequence = []

    def send_msg(self, receiver_addr, msg):
        send_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        send_socket.connect(receiver_addr)
        send_socket.sendall(msg.encode('utf-8'))
        send_socket.close()

    def process_accept(self, msg):
        print("# Learner {} with record {}".format(self.replicaID, self.accept_record))
        seq_num = msg['seq_num']
        replicaID = msg['replicaID']
        key = (msg['message'], msg['client'][0], msg['client'][1], msg['client'][2][0], msg['client'][2][1])
        if seq_num not in self.accept_record:
            self.accept_record[seq_num] = {}
        if key not in self.accept_record[seq_num]:
            self.accept_record[seq_num][key] = set()
        if replicaID not in self.accept_record[seq_num][key]:
            self.accept_record[seq_num][key].add(replicaID)
            if len(self.accept_record[seq_num][key]) == self.f+1:
                while seq_num >= len(self.learner_sequence):
                    self.learner_sequence.append({})
                self.learner_sequence[seq_num] = {
                    'message': msg['message'],
                    'client': msg['client']
                }
                print("# Learner {} learned seq num {}".format(self.replicaID, seq_num))
                if self.replicaID == self.view[0] and self.elected[0]:
                    new_msg = {
                        'type': 'RequestComplete',
                        'message': msg['message'],
                        'client': msg['client']
                    }
                    
                    self.send_msg((msg['client'][2][0], msg['client'][2][1]), json.dumps(new_msg))

    