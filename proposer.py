"""Proposer Implementation in MultiPaxos"""
import socket
import json
import time
import threading
import sys

from common import broadcast_msg



class Proposer:
    def __init__(self, replica, acceptor):
        self.f = replica.f
        self.num_replica = replica.num_replica
        self.replica_list = replica.replica_list
        self.replica_id = replica.replica_id
        self.view = replica.view
        self.addr = replica.addr

        self.pa_sequence = replica.pa_sequence
        self.client_record = replica.client_record
        self.acceptor_response = replica.acceptor_response

        self.readyCount = 1
        self.voteCount = 1
        self.acceptor = acceptor

        self.elected = replica.elected


    
    def election(self):
        """start election protocol, leader sends IAmLeader message, wait to collect more than f votes"""
        # clear acceptor response first
        self.acceptor_response = {}

        msg = {}
        msg['type'] = 'IAmLeader'
        msg['replica_id'] = self.replica_id
        msg['view'] = self.view[0]
        msg['addr'] = self.addr
        msg = json.dumps(msg)
        for idx, replicaAddr in enumerate(self.replica_list):
            if idx == self.replica_id:
                #do not send to itself
                continue
            send_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            send_socket.connect(replicaAddr)
            send_socket.sendall(msg.encode('utf-8'))
            send_socket.close()
        while self.voteCount < (self.f + 1):
            time.sleep(0.1) 
            # timeout?
        print("### Proposer {} is elected as leader".format(self.replica_id))
        # print("# chatLog value {}".format(self.chatLog[0]))
        sys.stdout.flush()
        self.elected[0] = True
        return True

    def add_vote(self, msg):
        # need check
        if len(self.acceptor_response) >= f + 1:
            return

        replica_id = msg['replica_id']
        accepted_vals = msg['accepted_vals']
        if replica_id not in acceptor_response:
            self.acceptor_response[replica_id] = accepted_vals
            self.voteCount += 1
        if len(self.acceptor_response) >= f + 1:
            self.start_propose()

    def start_propose(self):
        my_view = self.view[0]
        for replica_id in accepted_vals:
            replica_sequence = accepted_vals[replica_id]
            for seq_num, curr_seq in enumerate(replica_sequence):
                if curr_seq['view'] > self.pa_sequence[seq_num]['view']:
                    curr_seq['view'] = my_view
                    self.pa_sequence[seq_num] = curr_seq

        # 还没propose
        # gap 又要加空格，要不要换成dict


    def view_index(self):
        return self.view[0] % self.num_replica

    def process_client_request(self, msg):
        new_msg = {}
        new_msg['type'] = 'Proposal'
        new_msg['message'] = msg['message']
        new_msg['client_id'] = msg['client_id']
        new_msg['client_seq'] = msg['client_seq']
        new_msg['client_addr'] = msg['client_addr']
        new_msg['seq_num'] = len(self.pa_sequence)
        new_msg['view'] = self.view[0]
        self.pa_sequence.append({
                'client_id': new_msg['client_id'],
                'client_seq': new_msg['client_seq'],
                'client_addr': new_msg['client_addr'],
                'message': new_msg['message'],
                'view': new_msg['view']
        })
        print("# Proposer {} proposed seq_num {} for client {} request {} and message {}".format(self.replica_id, new_msg['seq_num'], new_msg['client_id'], new_msg['client_seq'], new_msg['message']))
        # for receiver_addr in self.replica_list:
        #     self.send_msg(receiver_addr, json.dumps(new_msg))
        # broadcast_thread = threading.Thread(target=self.broadcast_msg, args=(new_msg,))
        # broadcast_thread.start()
        broadcast_msg(new_msg, self.replica_list)

    def process_view_change_request(self, msg):
        new_view_num = msg['new_view_num']
        if new_view_num > self.view[0] and new_view_num % self.num_replica == self.replica_id:
            self.view[0] == new_view_num
            self.election()

    # def warm_up(self):
    #     self.readyCount += 1
    #     if self.readyCount == 2*self.f+1:
    #         self.election()
