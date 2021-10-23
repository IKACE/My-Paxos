"""Learner Implementation in MultiPaxos"""
import socket
import json
import time
import threading

from common import send_msg


class Learner:
    def __init__(self, replica):
        self.f = replica.f
        self.num_replica = replica.num_replica
        self.replica_list = replica.replica_list
        self.replica_id = replica.replica_id
        self.view = replica.view
        self.addr = replica.addr
        self.client_record = replica.client_record
        self.elected = replica.elected

        self.accept_record = {}
        self.learner_sequence = []


    def process_accept(self, msg):
        # print("# Learner {} with record {}".format(self.replica_id, self.accept_record))
        seq_num = msg['seq_num']
        replica_id = msg['replica_id']
        key = (msg['message'], msg['client_id'], msg['client_seq'], msg['client_addr'][0], msg['client_addr'][1])
        if seq_num not in self.accept_record:
            self.accept_record[seq_num] = {}
        if key not in self.accept_record[seq_num]:
            self.accept_record[seq_num][key] = set()
        if replica_id not in self.accept_record[seq_num][key]:
            self.accept_record[seq_num][key].add(replica_id)
            if len(self.accept_record[seq_num][key]) == self.f+1:
                while seq_num >= len(self.learner_sequence):
                    self.learner_sequence.append({})
                self.learner_sequence[seq_num] = {
                    'message': msg['message'],
                    'client_id': msg['client_id'],
                    'client_seq': msg['client_seq'],
                    'client_addr': msg['client_addr']
                }
                print("##### Learner {} learned seq num {} for client {} req {} and message {}".format(self.replica_id, seq_num, msg['client_id'], msg['client_seq'], msg['message']))
                print("##### Learner {} has sequence array hash value {}".format(self.replica_id, self.learner_sequence))
                print("##### Learner {} has sequence array hash value {}".format(self.replica_id, hash(str(self.learner_sequence))))
                if self.replica_id == self.view[0] and self.elected[0]:
                    self.reply_to_client(self, msg['message'], msg['client_id'], msg['client_seq'], msg['client_addr'])


    def reply_to_client(self, message, client_id. client_seq, client_addr):
        new_msg = {
            'type': 'RequestComplete',
            'message': msg['message'],
            'client_id': msg['client_id'],
            'client_seq': msg['client_seq'],
            'client_addr': msg['client_addr'],
        }
        send_msg((msg['client_addr'][0], msg['client_addr'][1]), json.dumps(new_msg))


    def process_request(self, msg):
        client_id = msg['client_id']
        client_seq = msg['client_seq']
        client_addr = msg['client_addr']
        if self.request_learned(client_id, client_seq):
            curr_request = self.client_record[client_id][client_seq]
            self.reply_to_client(curr_request['message'], client_id, client_seq, client_addr)
        else:
            self.notify_view_change(msg)


    def request_learned(self, client_id, client_seq):
        if client_id not in self.client_record:
            return False
        if client_seq not in self.client_record[client_id]:
            return False
        return True


    def add_client_request(self, client_id, client_seq, client_addr, message, seq_num):
        if client_id not in self.client_record:
            client_record[client_id] = {}
        if client_seq not in self.client_record[client_id]:
            self.client_record[client_id][client_seq] = {}
        curr_request = self.client_record[client_id][client_seq]
        curr_request['message'] = message
        curr_request['seq_num'] = seq_num
        curr_request['client_addr'] = client_addr
        print("#Learner{}: client {} request {} is learned at seq {}".format(self.replica_id, client_id, client_seq, seq_num))


    def notify_view_change(self, client_msg):
        new_view = self.view[0] + 1 
        msg = {}
        msg['type'] = 'LeaderChangeToYou'
        msg['replica_id'] = self.replica_id
        msg['client_msg'] = client_msg
        msg['new_view_num'] = new_view
        send_msg(self.replica_list[new_view % self.num_replica], json.dumps(msg))



    