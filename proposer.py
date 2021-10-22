"""Proposer Implementation in MultiPaxos"""
import socket
import json
import time
import threading
import sys



class Proposer:
    def __init__(self, replica, acceptor):
        self.f = replica.f
        self.replicaList = replica.replicaList
        self.replicaID = replica.replicaID
        self.view = replica.view
        self.addr = replica.addr

        self.pa_sequence = replica.pa_sequence
        self.client_record = replica.client_record

        self.readyCount = 1
        self.voteCount = 1
        self.acceptor = acceptor

        self.elected = replica.elected

    
    def election(self):
        """start election protocol, leader sends IAmLeader message, wait to collect more than f votes"""
        msg = {}
        msg['type'] = 'IAmLeader'
        msg['replicaID'] = self.replicaID
        msg['addr'] = self.addr
        msg = json.dumps(msg)
        for idx, replicaAddr in enumerate(self.replicaList):
            if idx == self.replicaID:
                #do not send to itself
                continue
            send_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            send_socket.connect(replicaAddr)
            send_socket.sendall(msg.encode('utf-8'))
            send_socket.close()
        while self.voteCount < (self.f + 1):
            time.sleep(0.1) 
            # timeout?
        print("### Proposer {} is elected as leader".format(self.replicaID))
        # print("# chatLog value {}".format(self.chatLog[0]))
        sys.stdout.flush()
        self.elected[0] = True
        return True

    def add_vote(self):
        self.voteCount += 1

    def view_index(self):
        return self.view[0] % self.num_replica



    def send_msg(self, receiver_addr, msg):
        send_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        send_socket.connect(receiver_addr)
        send_socket.sendall(msg.encode('utf-8'))
        send_socket.close()

    def process_client_request(self, msg):
        new_msg = {}
        new_msg['type'] = 'Proposal'
        new_msg['message'] = msg['message']
        new_msg['client'] = [msg['clientID'], msg['clientSeq'], msg['clientAddr']]
        new_msg['seq_num'] = len(self.pa_sequence)
        new_msg['view'] = self.view[0]
        for receiver_addr in self.replicaList:
            self.send_msg(receiver_addr, json.dumps(new_msg))

    # def warm_up(self):
    #     self.readyCount += 1
    #     if self.readyCount == 2*self.f+1:
    #         self.election()
