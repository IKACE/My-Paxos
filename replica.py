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
    def __init__(self, f, replicaList, replicaID, view):
        """init replica
         replicaList: ip and port tuples for each replica"""
        print("# Replica {} initializing".format(replicaID))
        sys.stdout.flush()
        self.f = f
        self.replicaList = replicaList
        self.num_replica = len(replicaList)
        self.replicaID = replicaID

        # mutable 
        self.view = [view]
        self.elected = [False]

        self.addr = (replicaList[replicaID][0], replicaList[replicaID][1])

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
        self.client_record = {}


        self.acceptor = Acceptor(self)
        self.learner = Learner(self)
        self.proposer = Proposer(self, self.acceptor)

        self.readyCount = 1


        # make sure we have all/>=f+1? processes then proceed
        self.warm_up()
        print("# Replica {} is warmed up and ready to proceed".format(self.replicaID))
  
        #if i am the leader
        if view == replicaID:
            self.proposer.election()
        
        self.listen_thread.join()

    # send warm-up message to leader, be ready for election
    def warm_up(self):
        # print("# Replica {} broadcasting ready up message".format(self.replicaID))
        # sys.stdout.flush()
        msg = {}
        msg['type'] = 'Ready'
        msg['replicaID'] = self.replicaID
        msg = json.dumps(msg)
        for idx, replicaAddr in enumerate(self.replicaList):
            if idx == self.replicaID:
                continue
            while True:

                time.sleep(1)
                send_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                try:
                    send_socket.connect(replicaAddr)
                except socket.error:
                    continue
                send_socket.sendall(msg.encode('utf-8'))
                print("# Replica {} send ready up message to {} {}".format(self.replicaID, idx, replicaAddr))
                send_socket.close()
                break
        # time.sleep(1)
        while self.readyCount != 2*self.f+1:
            time.sleep(1)


    def view_change(self, client_msg):
        self.view[0] += 1 
        msg = {}
        msg['type'] = 'YouAreLeader'
        msg['replicaID'] = self.replicaID
        msg['appendix'] = client_msg
        send_msg(self.replicaList[self.view_index()], json.dumps(msg))

    def view_index(self):
        return self.view[0] % self.num_replica

    def is_leader(self):
        if self.replicaID == self.view_index() and self.elected[0]:
            return True
        return False

    def listen(self):
        while True:

            # avoid busy waiting
            time.sleep(0.2)
            try:
                incoming_socket, _ = self.listen_socket.accept()
            except socket.timeout:
                continue
            message_chunks = []
            while True:
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
                self.proposer.add_vote()
            elif msg['type'] == 'Ready':
                print("# Replica {} received ready up message from {}".format(self.replicaID, msg['replicaID'])) 
                self.readyCount += 1
            elif msg['type'] == 'ClientRequest':
                # check if request has been processed
                if self.is_leader():
                    self.proposer.process_client_request(msg)
                else: # if replica is not curr view, forward to curr view
                    send_msg(self.replicaList[self.view_index()], json.dumps(msg))
            elif msg['type'] == 'ClientBroadcastRequest':
                # check if request has been processed
                # view change
                self.view_change(msg)
            elif msg['type'] == 'Proposal':
                self.acceptor.process_proposal(msg)
            elif msg['type'] == 'Accept':
                self.learner.process_accept(msg)





