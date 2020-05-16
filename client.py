import logging
import sys
import socket
import threading
import pickle

import yaml

logging.basicConfig(format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

port_mapping = {}
ip = None

def configure(client_number: int):
    global ip
    config = yaml.safe_load(open('config.yaml'))
    ip = config['default_ip']
    listening_port = config[client_number]
    logger.info('assigned port number %s', listening_port)
    for num, port in config.items():
        if isinstance(num, int):
            port_mapping[num] = port
    logger.debug('port mapping: %s', port_mapping)
    initialize(ip, port)

# TODO: needs to start thread for user input
def initialize(ip: str, port: int):
    """Starts up threads to listen for incoming messages and user input"""
    port_listener = threading.Thread(target = listener, args = [ip, port])
    port_listener.start()


def listener(ip: str, port: int):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as socket:
        socket.bind((ip, port))
        socket.listen()
        logger.debug("Listening on %s:%d", ip, port)
        while True:
            conn, addr = socket.accept()
            logger.debug("accepted incoming socket from %s", addr)
            processor = threading.Thread(target = event_enqueue, args=[conn, addr])
            processor.start()

def event_enqueue(conn: socket, addr):
    with conn:
        event = pickle.loads(conn.recv(1024))
        logger.debug("received event from %s", addr)

def send_event(event, destination: int):
    logger.debug("sending message to client %s", destination)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as socket:
        socket.connect((ip, port_mapping[destination]))
        socket.send(pickle.dumps(event))
        


def main(argv):
    if len(argv) == 1:
        logger.critical("No command line argument: missing client number")
        return
    configure(int(argv[1]))
    
if __name__ == "__main__":
    main(sys.argv)