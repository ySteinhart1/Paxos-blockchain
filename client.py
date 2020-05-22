import logging
import sys
import socket
import threading
import pickle
import time
from queue import Queue

import yaml
from ballot import ballot
from start_paxos import start_paxos
from proposal import proposal
from transaction import transaction
from promise import promise
from accept import accept
from accepted import accepted
from decision import decision
from typing import NewType


logging.basicConfig(format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

port_mapping = {}
ip = None
event_queue = Queue()
pending_transaction_queue = Queue()
ballotMap = {}
acceptedBals = {}

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
    initialize(ip, listening_port, client_number)

# TODO: needs to start thread for user input
def initialize(ip: str, port: int, pid: int):
    """Starts up threads to listen for incoming messages and user input"""
    port_listener = threading.Thread(target = listener, args = [ip, port])
    port_listener.start()
    consumer_thread = threading.Thread(target = consumer, args = [pid])
    consumer_thread.start()
    user_input()

def user_input():
    num = int(input())
    if num == 1:
        t1 = threading.Thread(target=send_event, args=["hello", 2])
        t2 = threading.Thread(target=send_event, args=["hello", 2])
        t1.start()
        t2.start()
    if num == 2:
        send_event("hello", 1)
    if num ==3:
        pending_transaction_queue.put(transaction(4))
        event_queue.put(start_paxos("begin"))

def listener(ip: str, port: int):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((ip, port))
        sock.listen()
        logger.debug("Listening on %s:%d", ip, port)
        while True:
            conn, addr = sock.accept()
            logger.debug("accepted incoming socket from %s", addr)
            processor = threading.Thread(target = event_enqueue, args=[conn, addr])
            processor.start()

def event_enqueue(conn: socket, addr):
    with conn:
        event = pickle.loads(conn.recv(1024))
        logger.debug("received event from %s", addr)
        event_queue.put(event)

def transaction_enqueue():
    transaction = pending_transaction_queue.get(True, None)



    

def send_event(event, destination: int):
    logger.debug("sending message to client %s", destination)
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((ip, port_mapping[destination]))
            sock.send(pickle.dumps(event))
    except (socket.error, socket.gaierror) as e:
        logger.debug("failed to send message")

        
def consumer(pid: int):
    ballotNum = ballot(0, 0)
    acceptNum = ballot(0, 0)
    acceptVal = None
    global ballotMap
    global acceptedBals
    current_transaction = None
    while True:
        event = event_queue.get(True, None)
        logger.debug("Processing event of type: %s", type(event))
        if isinstance(event, start_paxos):
            ballotNum = ballot(ballotNum.ballotNum + 1, pid)
            for process in range (1, 6):
                if process != pid:
                    sender = threading.Thread(target= send_event, args = [
                        proposal(ballotNum),
                        process
                    ])
                    sender.start()
            ballotMap[ballotNum] = []
            timeout = threading.Thread(target=timeout_proposal, args=[ballotNum])
            timeout.start()
        if isinstance(event, proposal):
            if event.ballot >= ballotNum:
                ballotNum = event.ballot
                sender = threading.Thread(target = send_event, args = [
                    promise(event.ballot, acceptNum, acceptVal),
                    event.ballot.proposer
                ])
                sender.start()
        elif isinstance(event, promise):
            ballotMap[event.ballot].append(event)
            if len(ballotMap[event.ballot]) == 2:
                maxpromise = max(ballotMap[event.ballot], key=lambda p: p.acceptNum)
                logger.debug("Max promise received: %s", maxpromise)
                if maxpromise.acceptVal:
                    current_transaction = maxpromise.acceptVal
                else:
                    current_transaction = compute_block()
                if ballotNum not in acceptedBals:
                    acceptedBals[ballotNum] = 0
                for process in range (1, 6):
                        if process != pid:
                            sender = threading.Thread(target= send_event, args = [
                                accept(ballotNum, current_transaction),
                                process
                            ])
                            sender.start()
                timeout = threading.Thread(target=timeout_acceptance, args=[ballotNum])
                timeout.start()
        elif isinstance(event, accept):
            if event.ballot >= ballotNum:
                acceptNum = event.ballot
                acceptVal = event.myVal
                sender = threading.Thread(target= send_event, args = [
                    accepted(event.ballot, event.myVal), event.ballot.proposer
                ])
                sender.start()
        elif isinstance(event, accepted):
            acceptedBals[event.ballot] += 1
            if acceptedBals[event.ballot] == 2:
                for process in range (1, 6):
                        if process != pid:
                            sender = threading.Thread(target= send_event, args = [
                                decision(ballotNum, current_transaction),
                                process
                            ])
                            sender.start()
                            acceptVal = None
        elif isinstance(event, decision):
            append_block(event.value)
            acceptVal = None
            
def timeout_proposal(ballotNum):
    global ballotMap
    time.sleep(5)
    if len(ballotMap[ballotNum]) < 2:
        event_queue.put(start_paxos("begin"))


def timeout_acceptance(ballotNum):
    global acceptedBals
    time.sleep(5)
    if acceptedBals[ballotNum] < 2:
        event_queue.put(start_paxos("begin"))

                
def compute_block() -> transaction:
    return transaction(1)

def append_block(transaction : transaction):
    pass



def main(argv):
    if len(argv) == 1:
        logger.critical("No command line argument: missing client number")
        return
    configure(int(argv[1]))
    
if __name__ == "__main__":
    main(sys.argv)