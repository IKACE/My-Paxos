import argparse
from time import time, sleep
from multiprocessing import Process
from replica import Replica

DEFAULT_NUM_CLIENT = 20

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
    replicaList = [('localhost',(x + 8000)) for x in range(total_num_replica)]

    # create list of replica processes
    # need to write run_replica (args to be modified)
    replica_process_list = []
    if not skip_slot and not message_loss:
        for replica_id in range(total_num_replica):
            p = Process(target=create_replica, args=(f, replicaList, replica_id, 0,))
            replica_process_list.append(p)

    # need to handle skip_slot and message_loss here

    # start all replica processes in the list
    for replica_process in replica_process_list:
        replica_process.start()

    # create list of client processes
    # need to write run_client (args to be modified)
    # each client know all replicas
    # client_process_list = []
    # for client_id in range(DEFAULT_NUM_CLIENT):
    #     p = Process(target=run_client, args=(client_id, total_num_replica, f, port_numbers, "127.0.0.1"))
    #     client_process_list.append(p)

    # # start all client processes in the list
    # for client_process in client_process_list:
    #     client_process.start()

    # # all clients done
    # for client_process in client_process_list:
    #     client_process.join()

    # all replica done
    for replica_process in replica_process_list:
        replica_process.join()

    # all done
    print("All processes finished")
def create_replica(f, replicaList, replicaID, view):
    replica = Replica(f, replicaList, replicaID, view)

if __name__ == "__main__":
    main()