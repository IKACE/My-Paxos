"""Proposer Implementation in MultiPaxos"""
import socket
import json
import time
import threading
import sys

from replica import MAXIMUM_LOG_SIZE

class Proposer:
    def __init__(self, replica, acceptor):
        self.f = replica.f
        self.replicaList = replica.replicaList
        self.replicaID = replica.replicaID
        self.view = replica.view
        self.addr = replica.addr
        self.readyCount = 1
        self.voteCount = 1
        self.acceptor = acceptor

        self.elected = False
        self.clients = {}
    
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
        print("# Proposer {} is elected as leader".format(self.replicaID))
        sys.stdout.flush()
        self.elected = True
        return True

    def add_vote(self):
        self.voteCount += 1

    def is_elected(self):
        return self.elected

    def propose(self, msg):
        chatLog = self.acceptor.read_chatLog()

    def process_client_request(self, msg):
        m = msg['message']
        client_id = msg['clientID']
        client_seq = msg['clientSeq']
        client_addr = msg['clientAddr']
        if 

    # def warm_up(self):
    #     self.readyCount += 1
    #     if self.readyCount == 2*self.f+1:
    #         self.election()
