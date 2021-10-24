"""Replica Implementation in MultiPaxos"""
import socket
import json
import time
import threading
import sys
from proposer import Proposer
from learner import Learner
from acceptor import Acceptor
from common import send_msg


class Replica:
    def __init__(self, f, replica_list, replica_id, view, skip_slot, msg_loss):
        """init replica
         replica_list: ip and port tuples for each replica"""
        print("# Replica {} initializing".format(replica_id))
        sys.stdout.flush()
        self.f = f
        self.replica_list = replica_list
        self.num_replica = len(replica_list)
        self.replica_id = replica_id
        self.shut_down = [False]
        
        # test case 4 & 5
        self.skip_slot = skip_slot
        self.msg_loss = msg_loss

        # mutable 
        self.view = [view]
        self.elected = [False]

        self.addr = (replica_list[replica_id][0], replica_list[replica_id][1])

        self.listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listen_socket.bind(self.addr)
        self.listen_socket.listen(100)
        # assume timeout 1, less than client timeout time
        # self.listen_socket.settimeout(5)
        self.listen_thread = threading.Thread(target=self.listen, args=())
        self.listen_thread.start()

        # a array of proposed values shared by proposer and acceptor
        self.pa_sequence = []

        # record of clients requests
        # format: dic client_id -> {client_seq []]}
        self.client_record = {}
        # list of received client address
        self.client_addr = []

        # a record of acceptor response during election
        self.acceptor_response = {}

        self.acceptor = Acceptor(self)
        self.learner = Learner(self)
        self.proposer = Proposer(self, self.acceptor)

        self.readyCount = 1


        # make sure we have all/>=f+1? processes then proceed
        self.warm_up()
        print("# Replica {} is warmed up and ready to proceed".format(self.replica_id))
  
        #if i am the leader
        if view == replica_id:
            self.proposer.election()
        
        self.listen_thread.join()

    # send warm-up message to leader, be ready for election
    def warm_up(self):
        # print("# Replica {} broadcasting ready up message".format(self.replica_id))
        # sys.stdout.flush()
        msg = {}
        msg['type'] = 'Ready'
        msg['replica_id'] = self.replica_id
        msg = json.dumps(msg)
        for idx, replicaAddr in enumerate(self.replica_list):
            if idx == self.replica_id:
                continue
            while True:

                time.sleep(1)
                send_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                try:
                    send_socket.connect(replicaAddr)
                except socket.error:
                    continue
                send_socket.sendall(msg.encode('utf-8'))
                print("# Replica {} send ready up message to {} {}".format(self.replica_id, idx, replicaAddr))
                send_socket.close()
                break
        # time.sleep(1)
        while self.readyCount != 2*self.f+1:
            time.sleep(1)


    def view_index(self):
        return self.view[0] % self.num_replica

    def is_leader(self):
        if self.replica_id == self.view_index() and self.elected[0]:
            return True
        return False

    def listen(self):
        while self.shut_down[0] == False:

            # avoid busy waiting
            time.sleep(0.2)
            try:
                incoming_socket, _ = self.listen_socket.accept()
            except socket.timeout:
                continue
            message_chunks = []
            while self.shut_down[0] == False:
                try:
                    msg = incoming_socket.recv(4096)
                except socket.timeout:
                    continue
                if not msg:
                    break
                message_chunks.append(msg)
            incoming_socket.close()
            message_bytes = b''.join(message_chunks)
            message_str = message_bytes.decode('utf-8')
            try:
                msg = json.loads(message_str)
            except json.JSONDecodeError:
                continue
            if msg['type'] == 'IAmLeader':
                self.acceptor.change_leader(msg)
            elif msg['type'] == 'YouAreLeader':
                self.proposer.add_vote(msg)
            elif msg['type'] == 'Ready':
                print("# Replica {} received ready up message from {}".format(self.replica_id, msg['replica_id'])) 
                self.readyCount += 1
            elif msg['type'] == 'ClientRequest':
                # check if request has been processed
                client_view = msg['client_view']
                if client_view == self.view[0]:
                    if self.is_leader():
                        self.proposer.process_client_request(msg)
                    else: # if replica is not curr view, forward to curr view
                        # happen mostly when new client is in, or when new leader election result is lost due to    asynchronous
                        self.learner.process_request(msg)
                else:        
                    new_msg = {}
                    new_msg['type'] = 'ViewChange'
                    new_msg['view'] = self.view[0]
                    send_msg((msg['client_addr'][0], msg['client_addr'][1]), new_msg, self.msg_loss)
            # elif msg['type'] == 'ClientBroadcastRequest':
            #     # check if request has been processed
            #     # learner check whether this request has been processed already
            #     self.learner.process_request(msg)
            elif msg['type'] == 'Proposal':
                self.acceptor.process_proposal(msg)
            elif msg['type'] == 'Accept':
                self.learner.process_accept(msg)
            elif msg['type'] == 'LeaderChangeToYou':
                self.proposer.process_view_change_request(msg)

