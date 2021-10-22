"""Client Implementation in MultiPaxos"""
import socket
import json
import time
import threading

REQUEST_TIMEOUT = 60

class Client:
    

    def __init__(self, replicaList, clientID, view, IP, port):
        """INPUT: replicaList: a list of tuple containing IP and port for replica, 
        clientID: unique identifier for client, view: leader number, 
        IP: client IP, port: client port"""
        print("### Client", clientID, "initializing")
        self.replicaList = replicaList
        self.clientID = clientID
        self.view = view
        self.addr = (IP, port)
        self.seq = 0
        self.finished = False

        self.listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listen_socket.bind(self.addr)
        self.listen_socket.listen(5)
        # assume timeout 5, timeout for client should be longer than in replica
        self.listen_socket.settimeout(5)
        self.listen_thread = threading.Thread(target=self.listen, args=())
        self.listen_thread.start()

        # self.listen_thread.join()

    def send_message(self, m):
        """method for sending a single message, m: string"""
        print("### Client", self.clientID, "sending request #", self.seq, "message", m)
        msg = {}
        msg['type'] = 'ClientRequest'
        msg['message'] = m
        msg['clientID'] = self.clientID
        msg['clientSeq'] = self.seq
        msg['clientAddr'] = self.addr
        # prepare to send message
        send_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        send_socket.connect(self.replicaList[self.view])
        msg = json.dumps(msg)
        send_socket.sendall(msg.encode('utf-8'))
        send_socket.close()
        self.finished = False
        # callback ?
        time_sent = time.time()
        while self.finished == False:
            if time.time() - time_sent >= REQUEST_TIMEOUT:
                self.send_request_to_all(m)
                time_sent = time.time()
            # avoid busy waiting
            time.sleep(1)
            continue
        print("### Client", self.clientID, "request #", self.seq, "complete")
        self.seq += 1

    def send_batch_messages(self, mList):
        """method for sending batch messages, mList: list of messages """
        for m in mList:
            self.send_message(self, m)


    def send_request_to_all(self, m):
        msg = {}
        msg['type'] = 'ClientBroadcastRequest'
        msg['message'] = m
        msg['clientID'] = self.clientID
        msg['clientSeq'] = self.seq
        msg['clientAddr'] = self.addr
        msg = json.dumps(msg)
        for idx, replicaAddr in enumerate(self.replicaList):
            send_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            send_socket.connect(replicaAddr)
            send_socket.sendall(msg.encode('utf-8'))
            send_socket.close()


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
            if msg['type'] == 'RequestComplete':
                self.finished = True
