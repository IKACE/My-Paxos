"""Learner Implementation in MultiPaxos"""
import socket
import json
import time
import threading
import sys
import os

from common import send_msg

VIEW_CHANGE_INTERVAL = 20

class Learner:
    def __init__(self, replica):
        self.f = replica.f
        self.num_replica = replica.num_replica
        self.replica_list = replica.replica_list
        self.replica_id = replica.replica_id
        self.view = replica.view
        self.addr = replica.addr
        self.client_record = replica.client_record
        self.client_addr = replica.client_addr
        self.elected = replica.elected

        self.msg_loss = replica.msg_loss

        # log file
        self.log_dir = replica.log_dir
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
        self.log_file_path = os.path.join(self.log_dir, "learner{}.txt".format(self.replica_id))
        if os.path.exists(self.log_file_path):
            os.remove(self.log_file_path)


        # count how many replica accepts this proposal
        self.accept_record = {}
        # learned sequence as a buffer
        self.learned_sequence = []
        # this is the real chat log, must be executed in exact monotonic increasing order, starting from 0
        self.executed_sequence = []
        # a simpler array of execution history for debugging
        self.execution_history = []

        self.last_view_change = replica.last_view_change


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
                while seq_num >= len(self.learned_sequence):
                    self.learned_sequence.append({})
                seq_content = {
                    'message': msg['message'],
                    'client_id': msg['client_id'],
                    'client_seq': msg['client_seq'],
                    'client_addr': msg['client_addr'],
                    'view': msg['view']
                }
                self.learned_sequence[seq_num] = seq_content
                # print("# Learner {} learned seq num {} for client {} req {} and message {}".format(self.replica_id, seq_num, msg['client_id'], msg['client_seq'], msg['message']))
                # print("# Learner {} has sequence array  value {}".format(self.replica_id, self.learned_sequence))
                # print("# Learner {} has sequence array hash value {}".format(self.replica_id, hash(str(self.learned_sequence))))
                # all learners reply to client

                if seq_num == len(self.executed_sequence):
                    self.execute_request(seq_content)
                    # clear all buffer waitings
                    while len(self.executed_sequence) < len(self.learned_sequence):
                        start_idx = len(self.executed_sequence)
                        if self.learned_sequence[start_idx] == {}:
                            break
                        seq_content = self.learned_sequence[start_idx]
                        self.execute_request(seq_content)

    def execute_request(self, seq_content):
        """Execute request, add to chat log, reply back to client"""
        self.executed_sequence.append(seq_content)
        self.execution_history.append((len(self.executed_sequence)-1, seq_content['client_id'], seq_content['client_seq']))
        self.update_client_record(seq_content['client_id'], seq_content['client_seq'], seq_content['client_addr'])
        # # print("### Learner {} EXECUTED seq num {} for client {} req {} and message {}".format(self.replica_id, len(self.executed_sequence)-1, seq_content['client_id'], seq_content['client_seq'], seq_content['message']))
        # print("##### Learner {} EXECUTION HISTORY {}".format(self.replica_id, self.execution_history))
        if len(self.execution_history) % 2 == 0:
            print("##### Learner {} EXECUTION HISTORY SEQ NUM {} HASH {} ".format(self.replica_id, len(self.execution_history), self.hash(str(self.execution_history))))
            # print("##### Learner {} EXECUTION HISTORY {}".format(self.replica_id, self.execution_history))
            sys.stdout.flush()
            with open(self.log_file_path, 'a') as f:
                f.write("##### Learner {} EXECUTION HISTORY SEQ NUM {} HASH {} \n".format(self.replica_id, len(self.execution_history), self.hash(str(self.execution_history))))
                f.close()
        self.reply_to_client(seq_content)



    def reply_to_client(self, msg):
        new_msg = {
            'type': 'RequestComplete',
            'message': msg['message'],
            'client_id': msg['client_id'],
            'client_seq': msg['client_seq'],
            'client_addr': msg['client_addr'],
            'view': self.view[0]
        }
        send_msg((msg['client_addr'][0], msg['client_addr'][1]), new_msg, self.msg_loss)


    def process_request(self, msg):
        client_id = msg['client_id']
        client_seq = msg['client_seq']
        client_addr = msg['client_addr']
        # if already executed, Learner asserts that reponse to client is lost due to asynchronous network
        if self.request_executed(client_id, client_seq):
            self.reply_to_client(msg)
        elif time.time() - self.last_view_change[0] > VIEW_CHANGE_INTERVAL:
            self.notify_view_change(msg)


    def request_executed(self, client_id, client_seq):
        if client_id not in self.client_record:
            return False
        if client_seq not in self.client_record[client_id]:
            return False
        return True


    def update_client_record(self, client_id, client_seq, client_addr):
        if client_id not in self.client_record:
            self.client_record[client_id] = []
        if client_seq not in self.client_record[client_id]:
            self.client_record[client_id].append(client_seq)
        if client_addr not in self.client_addr:
            self.client_addr.append(client_addr)


    def notify_view_change(self, client_msg):
        new_view = self.view[0] + int((time.time()-self.last_view_change[0]) // VIEW_CHANGE_INTERVAL)
        # new_view = self.view[0] + 1
        msg = {}
        msg['type'] = 'LeaderChangeToYou'
        msg['replica_id'] = self.replica_id
        # does new leader has to process client req right away?
        msg['client_msg'] = client_msg
        msg['new_view_num'] = new_view
        send_msg(self.replica_list[new_view % self.num_replica], msg, self.msg_loss)

    def hash(self, key):
        return sum(bytearray(key.encode('utf-8'))) % 699733

    