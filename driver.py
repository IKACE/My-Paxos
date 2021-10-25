import argparse
import random
from time import time, sleep
from multiprocessing import Process
from client import Client
from replica import Replica

DEFAULT_NUM_CLIENT = 20

# ["--skip_slot", "0",
                    #  "--f", "3",
                    #  "--msg_loss", "20"] 3 clients

# TEST_TYPE = 'SINGLE CLIENT SINGLE REQ'
# TEST_TYPE = 'SINGLE CLIENT MULTIPLE REQ'
# TEST_TYPE = 'MULTIPLE CLIENT SINGLE REQ'
# TEST_TYPE = 'MULTIPLE CLIENT MULTIPLE REQ'
# TEST_TYPE = 'PROPOSER 0 FAIL BEFORE PROPOSAL'
# TEST_TYPE = 'PROPOSER 0 AND 1 FAIL BEFORE PROPOSAL'
# TEST_TYPE= 'PROPOSER 0 FAIL AFTER PROPOSAL'
# TEST_TYPE = 'PROPOSER 0 SKIP SLOT 0'
TEST_TYPE = 'STRESS TEST 0'

def main():
    """ parse the ip and port to connect to """
    parser = argparse.ArgumentParser()
    parser.add_argument('--f', type=int, default=2,
                        help='number of tolerated failures')
    parser.add_argument('--skip_slot', type=int, default=-1,
                        help='test for skiping slot, input is an integer for primary to skip proposing this slot')
    parser.add_argument('--msg_loss', type=int, default=-1,
                        help='test for message loss, input is a probability in percentage for message to be lost')
    parser.add_argument('--rand_seed', type=int, default=591,
                        help='random seed')
    args = parser.parse_args()
    f = args.f
    total_num_replica = f * 2 + 1

    skip_slot = args.skip_slot
    msg_loss = args.msg_loss
    msg_loss /= 100
    random.seed(args.rand_seed)


    replica_list = [('localhost',(x + 8000)) for x in range(total_num_replica)]

    # create list of replica processes
    # need to write run_replica (args to be modified)
    replica_process_list = []

    for replica_id in range(total_num_replica):
        p = Process(target=create_replica, args=(f, replica_list, replica_id, 0, skip_slot, msg_loss))
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
            p = Process(target=send_single_message, args=(replica_list, client_id, 0, 'localhost', (2345+client_id), msg, msg_loss, f))
            client_process_list.append(p) 
    elif TEST_TYPE == 'SINGLE CLIENT MULTIPLE REQ':
        message_list = ['Hello 0', 'Hello 1', 'Hello 2', 'Hello 3']
        for client_id in range(1):
            p = Process(target=send_batch_message, args=(replica_list, client_id, 0, 'localhost', (2345+client_id), message_list, msg_loss, f))
            client_process_list.append(p)
    elif TEST_TYPE == 'MULTIPLE CLIENT SINGLE REQ':
        msg = "Hello World!"
        for client_id in range(5):
            p = Process(target=send_single_message, args=(replica_list, client_id, 0, 'localhost', (2345+client_id), msg, msg_loss, f))
            client_process_list.append(p)
    elif TEST_TYPE == 'MULTIPLE CLIENT MULTIPLE REQ':
        message_list = ['Hello 0', 'Hello 1', 'Hello 2', 'Hello 3']
        for client_id in range(3):
            p = Process(target=send_batch_message, args=(replica_list, client_id, 0, 'localhost', (2345+client_id), message_list, msg_loss, f))
            client_process_list.append(p)
    elif TEST_TYPE == 'PROPOSER 0 FAIL BEFORE PROPOSAL':
        msg = "PROPOSER 0 FAIL BEFORE PROPOSAL"
        for client_id in range(3):
            p = Process(target=send_single_message, args=(replica_list, client_id, 0, 'localhost', (2345+client_id), msg, msg_loss, f))
            client_process_list.append(p) 
    elif TEST_TYPE == 'PROPOSER 0 FAIL AFTER PROPOSAL':
        message_list = ['PROPOSER 0 FAIL AFTER PROPOSAL', 'Hello 1', 'Hello 2', 'Hello 3']
        for client_id in range(1):
            p = Process(target=send_batch_message, args=(replica_list, client_id, 0, 'localhost', (2345+client_id), message_list, msg_loss, f))
            client_process_list.append(p) 
    elif TEST_TYPE == 'PROPOSER 0 AND 1 FAIL BEFORE PROPOSAL':
        msg = "PROPOSER 0 AND 1 FAIL BEFORE PROPOSAL"
        for client_id in range(3):
            p = Process(target=send_single_message, args=(replica_list, client_id, 0, 'localhost', (2345+client_id), msg, msg_loss, f))
            client_process_list.append(p) 
    elif TEST_TYPE == 'PROPOSER 0 SKIP SLOT 0':
        message_list = ['Hello 0', 'Hello 1', 'Hello 2', 'Hello 3']

        p = Process(target=send_batch_message, args=(replica_list, 0, 0, 'localhost', (2345+0), message_list, msg_loss, f))
        client_process_list.append(p)

        p = Process(target=send_batch_message, args=(replica_list, 1, 0, 'localhost', (2345+1), message_list, msg_loss, f))
        client_process_list.append(p)
    elif TEST_TYPE == 'STRESS TEST 0':
        for client_id in range(3):
            p = Process(target=send_random_message, args=(replica_list, client_id, 0, 'localhost', (2345+client_id), msg_loss, f))
            client_process_list.append(p)     
    # start all client processes in the list
    for idx, client_process in enumerate(client_process_list):
        client_process.start()
        if idx == 0 and (TEST_TYPE == 'PROPOSER 0 SKIP SLOT 0' or TEST_TYPE == 'STRESS TEST 0'):
            sleep(15)

    # all clients done
    for client_process in client_process_list:
        client_process.join()

    # all replica done
    for replica_process in replica_process_list:
        replica_process.join()

    # all done
    print("All processes finished")
def create_replica(f, replica_list, replica_id, view, skip_slot, msg_loss):
    replica = Replica(f, replica_list, replica_id, view, skip_slot, msg_loss)

def send_single_message(replica_list, client_id, view, IP, port, msg, msg_loss, f):
    client = Client(replica_list, client_id, view, IP, port, msg_loss, f)
    client.send_message(msg)

def send_batch_message(replica_list, client_id, view, IP, port, message_list, msg_loss, f):
    client = Client(replica_list, client_id, view, IP, port, msg_loss, f)
    client.send_batch_messages(message_list)

def send_random_message(replica_list, client_id, view, IP, port, msg_loss, f):
    client = Client(replica_list, client_id, view, IP, port, msg_loss, f)
    count = 0
    while count < 100:
        sleep(random.randrange(1, 10))
        client.send_message('Hello '+str(count))
        count += 1




if __name__ == "__main__":
    main()