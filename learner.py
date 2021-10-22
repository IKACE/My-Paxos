"""Learner Implementation in MultiPaxos"""
import socket
import json
import time
import threading

from replica import MAXIMUM_LOG_SIZE

class Learner:
    def __init__(self, replica):
        self.f = replica.f
        self.replicaList = replica.replicaList
        self.replicaID = replica.replicaID
        self.view = replica.view
        self.addr = replica.addr

        self.chatLog = [MAXIMUM_LOG_SIZE]

    def print_chatLog(self):
        print(self.chatLog)
    