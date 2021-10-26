import argparse
from replica import Replica

def main():
    """ parse the ip and port to connect to """
    parser = argparse.ArgumentParser()
    parser.add_argument('--f', type=int, default=2,
                        help='number of tolerated failures')
    parser.add_argument('--skip_slot', type=int, default=-1,
                        help='test for skiping slot, input is an integer for primary to skip proposing this slot, only work if it is the initial primary replica #0')
    parser.add_argument('--msg_loss', type=int, default=-1,
                        help='test for message loss, input is a probability in percentage for message to be lost')
    parser.add_argument('--config_path', type=str, default="./configs/config.txt",
                        help='path of configuration file each line containing one pair of ip and port') 
    parser.add_argument('--log_dir', type=str, default="./logs",
                        help='path of log directory to write chat log to')
    parser.add_argument('--replica_id', type=int, default=-1,
                        help='replica id')
    args = parser.parse_args()
    f = args.f
    replica_id = args.replica_id
    total_num_replica = f * 2 + 1
    skip_slot = args.skip_slot
    msg_loss = args.msg_loss
    msg_loss /= 100

    # read config file
    try:
        config_f = open(args.config_path, 'r')
    except OSError:
        print("Could not read configuration file, exiting")
        return 1
    replica_list = []
    for line in config_f.readlines():
        line = line.split()
        replica_list.append((line[0], int(line[1])))
    config_f.close()
    if len(replica_list) != total_num_replica:
        print("number of replicas in config file does not match parameter f, exiting")
        return 1
    # log directory
    log_dir = args.log_dir

    view = 0

    if replica_id < 0 or replica_id >= total_num_replica:
        print("Must provide a replica id within range of 0 and total number of replicas (exclusive)")
        return 1

    replica = Replica(f, replica_list, replica_id, view, skip_slot, msg_loss, log_dir)        

if __name__ == "__main__":
    main()