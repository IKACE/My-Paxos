"""Acceptor Implementation in MultiPaxos"""
import socket
import json
import time
import threading
import sys

from common import broadcast_msg


class Acceptor:
    def __init__(self, replica):
        self.f = replica.f
        self.replica_list = replica.replica_list
        self.replica_id = replica.replica_id
        self.view = replica.view
        self.addr = replica.addr

        self.pa_sequence = replica.pa_sequence
        self.client_record = replica.client_record

    def change_leader(self, msg):
        # modular?
        new_view = msg['view']
        leader_addr = msg['addr']

        if self.view[0] <= new_view:
            print("# Acceptor {} accepts {} as new leader".format(self.replica_id, msg['view']))
            sys.stdout.flush()
            self.view[0] = new_view

            # need check
            new_msg = {}
            new_msg['type'] = 'YouAreLeader'
            new_msg['replica_id'] = self.replica_id
            new_msg['view'] = new_view
            msg['accepted_vals'] = self.pa_sequence
            send_msg(leader_addr, json.dumps(new_msg))

        # what is this for
            return True
        return False



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
                'client_id': msg['client_id'],
                'client_seq': msg['client_seq'],
                'client_addr': msg['client_addr'],
                'message': msg['message'],
                'view': msg['view']
        }
        new_msg = {}
        new_msg['type'] = 'Accept'
        new_msg['replica_id'] = self.replica_id
        new_msg['message'] = msg['message']
        new_msg['client_id'] = msg['client_id']
        new_msg['client_seq'] = msg['client_seq']
        new_msg['client_addr'] = msg['client_addr']
        new_msg['view'] = msg['view']
        new_msg['seq_num'] = msg['seq_num']

        # broadcast_thread = threading.Thread(target=self.broadcast_msg, args=(new_msg,))
        # broadcast_thread.start()
        broadcast_msg(new_msg, self.replica_list)
        