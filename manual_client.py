import argparse
from client import Client

def main():
    """ parse the ip and port to connect to """
    parser = argparse.ArgumentParser()
    parser.add_argument('--f', type=int, default=2,
                        help='number of tolerated failures')
    parser.add_argument('--msg_loss', type=int, default=-1,
                        help='test for message loss, input is a probability in percentage for message to be lost')
    parser.add_argument('--config_path', type=str, default="./configs/config.txt",
                        help='path of configuration file each line containing one pair of ip and port') 
    parser.add_argument('--client_id', type=int, default=-1,
                        help='client id')
    parser.add_argument('--ip', type=str, default="localhost",
                        help='IP for client')
    parser.add_argument('--port', type=int, default=2000,
                        help='port for client')
    args = parser.parse_args()
    f = args.f
    total_num_replica = f * 2 + 1
    ip = args.ip
    port = args.port
    client_id = args.client_id
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


    view = 0

    if client_id < 0:
        print("Must provide a replica id greater than or equal to 0")
        return 1

    client = Client(replica_list, client_id, view, ip, port, msg_loss, f)
    while True:
        msg = input("Enter your message:")
        if msg == "SHUTDOWN":
            break
        client.send_message(msg)       
    print("# Client {} exiting".format(client_id))
if __name__ == "__main__":
    main()