"""Client Implementation in MultiPaxos"""
import socket
import json
import time
import threading

REQUEST_TIMEOUT = 10
from common import send_msg, broadcast_msg

class Client:
    

    def __init__(self, replica_list, client_id, view, IP, port, msg_loss, f):
        """INPUT: replica_list: a list of tuple containing IP and port for replica, 
        client_id: unique identifier for client, view: leader number, 
        IP: client IP, port: client port"""
        print("### Client", client_id, "initializing")
        self.num_replicas = 2*f + 1
        self.replica_list = replica_list
        self.client_id = client_id
        self.view = view
        self.addr = (IP, port)
        self.seq = 0

        self.finished = False

        self.view_change = False

        # test case 5
        self.msg_loss = msg_loss

        self.listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listen_socket.bind(self.addr)
        self.listen_socket.listen(10000)
        # assume timeout 5, timeout for client should be longer than in replica
        self.listen_socket.settimeout(5)
        self.listen_thread = threading.Thread(target=self.listen, args=())
        self.listen_thread.start()

        # self.listen_thread.join()

    def send_message(self, m):
        """method for sending a single message, m: string"""
        print("### Client", self.client_id, "sending request #", self.seq, "message", m)
        msg = {}
        msg['type'] = 'ClientRequest'
        msg['message'] = m
        msg['client_id'] = self.client_id
        msg['client_seq'] = self.seq
        msg['client_addr'] = self.addr
        msg['client_view'] = self.view
        # prepare to send message
        send_msg(self.replica_list[self.view_index()], msg, self.msg_loss)

        self.finished = False
        # callback ?
        time_sent = time.time()
        while self.finished == False:
            if self.view_change == True:
                self.view_change = False
                msg['client_view'] = self.view
                send_msg(self.replica_list[self.view_index()], msg, self.msg_loss)
                time_sent = time.time()

            if time.time() - time_sent >= REQUEST_TIMEOUT:
                print("# Client {} broadcast request {}".format(self.client_id, self.seq))
                self.send_request_to_all(m)
                time_sent = time.time()
            # avoid busy waiting
            time.sleep(0.1)
            continue
        print("### Client {} request {} complete".format(self.client_id, self.seq))
        self.seq += 1
    def view_index(self):
        return self.view % self.num_replicas

    def send_batch_messages(self, mList):
        """method for sending batch messages, mList: list of messages """
        for m in mList:
            self.send_message(m)


    def send_request_to_all(self, m):
        msg = {}
        msg['type'] = 'ClientRequest'
        msg['message'] = m
        msg['client_id'] = self.client_id
        msg['client_seq'] = self.seq
        msg['client_addr'] = self.addr
        msg['client_view'] = self.view
        broadcast_msg(self.replica_list, msg, self.msg_loss)


    def listen(self):
        while True:
            # avoid busy waiting
            # avoid busy waiting
            time.sleep(1)
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
            # check seq number in case of redundant replies
            if msg['type'] == 'RequestComplete' and msg['client_seq'] == self.seq:
                self.finished = True
                if msg['view'] > self.view:
                    self.view = msg['view']

            if msg['type'] == 'ViewChange' and msg['view'] > self.view:
                self.view = msg['view']
                self.view_change = True