import argparse
from time import time, sleep
from multiprocessing import Process
from client import Client
from replica import Replica

DEFAULT_NUM_CLIENT = 20

# TEST_TYPE = 'SINGLE CLIENT SINGLE REQ'
# TEST_TYPE = 'SINGLE CLIENT MULTIPLE REQ'
# TEST_TYPE = 'MULTIPLE CLIENT SINGLE REQ'
# TEST_TYPE = 'MULTIPLE CLIENT MULTIPLE REQ'
TEST_TYPE = 'PROPOSER 0 FAIL BEFORE PROPOSAL'

def main():
    """ parse the ip and port to connect to """
    parser = argparse.ArgumentParser()
    parser.add_argument('--f', type=int, default=1,
                        help='number of tolerated failures')
    parser.add_argument('--skip', type=bool, default=False,
                        help='test for skiping slot')
    parser.add_argument('--meslos', type=bool, default=False,
                        help='test for message loss')
    args = parser.parse_args()
    f = args.f
    total_num_replica = f * 2 + 1
    skip_slot = args.skip
    message_loss = args.meslos
    replica_list = [('localhost',(x + 8000)) for x in range(total_num_replica)]

    # create list of replica processes
    # need to write run_replica (args to be modified)
    replica_process_list = []
    if not skip_slot and not message_loss:
        for replica_id in range(total_num_replica):
            p = Process(target=create_replica, args=(f, replica_list, replica_id, 0,))
            replica_process_list.append(p)

    # need to handle skip_slot and message_loss here

    # start all replica processes in the list
    for replica_process in replica_process_list:
        replica_process.start()

    # create list of client processes
    # need to write run_client (args to be modified)
    # each client know all replicas
    client_process_list = []
    sleep(10)

    if TEST_TYPE == 'SINGLE CLIENT SINGLE REQ':
        msg = "Hello World!"
        for client_id in range(1):
            p = Process(target=send_single_message, args=(replica_list, client_id, 0, 'localhost', (2345+client_id), msg))
            client_process_list.append(p) 
    elif TEST_TYPE == 'SINGLE CLIENT MULTIPLE REQ':
        message_list = ['Hello 0', 'Hello 1', 'Hello 2', 'Hello 3']
        for client_id in range(1):
            p = Process(target=send_batch_message, args=(replica_list, client_id, 0, 'localhost', (2345+client_id), message_list))
            client_process_list.append(p)
    elif TEST_TYPE == 'MULTIPLE CLIENT SINGLE REQ':
        msg = "Hello World!"
        for client_id in range(5):
            p = Process(target=send_single_message, args=(replica_list, client_id, 0, 'localhost', (2345+client_id), msg))
            client_process_list.append(p)
    elif TEST_TYPE == 'MULTIPLE CLIENT MULTIPLE REQ':
        message_list = ['Hello 0', 'Hello 1', 'Hello 2', 'Hello 3']
        for client_id in range(3):
            p = Process(target=send_batch_message, args=(replica_list, client_id, 0, 'localhost', (2345+client_id), message_list))
            client_process_list.append(p)
    elif TEST_TYPE == 'PROPOSER 0 FAIL BEFORE PROPOSAL':
        msg = "PROPOSER 0 FAIL BEFORE PROPOSAL"
        for client_id in range(3):
            p = Process(target=send_single_message, args=(replica_list, client_id, 0, 'localhost', (2345+client_id), msg))
            client_process_list.append(p) 

    # start all client processes in the list
    for client_process in client_process_list:
        client_process.start()

    # all clients done
    for client_process in client_process_list:
        client_process.join()

    # all replica done
    for replica_process in replica_process_list:
        replica_process.join()

    # all done
    print("All processes finished")
def create_replica(f, replica_list, replica_id, view):
    replica = Replica(f, replica_list, replica_id, view)

def send_single_message(replica_list, client_id, view, IP, port, msg):
    client = Client(replica_list, client_id, view, IP, port)
    client.send_message(msg)

def send_batch_message(replica_list, client_id, view, IP, port, message_list):
    client = Client(replica_list, client_id, view, IP, port)
    client.send_batch_messages(message_list)



if __name__ == "__main__":
    main()