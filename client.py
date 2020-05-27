import logging
import re
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
from stale import stale
from request import request
from typing import NewType
from blockchain import node, blockchain
from message import message


logging.basicConfig(format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

port_mapping = {}
link_status = {}
ip = None
event_queue = Queue()
pending_transaction_queue = Queue()
ballotMap = {}
acceptedBals = {}
blockchain = blockchain()
ballotNum = ballot(0, 0, 0)
acceptNum = ballot(0, 0, 0)
acceptVal = None
current_transaction = None
balance = 100
pid = 0

def configure(client_number: int):
    global ip
    global pid
    pid = client_number
    config = yaml.safe_load(open('config.yaml'))
    ip = config['default_ip']
    listening_port = config[client_number]
    logger.info('assigned port number %s', listening_port)
    for num, port in config.items():
        if isinstance(num, int):
            port_mapping[num] = port
            link_status[num] = True
    logger.debug('port mapping: %s', port_mapping)
    logger.debug('initial link statuses: %s', link_status)
    initialize(ip, listening_port, client_number)

# TODO: needs to start thread for user input
def initialize(ip: str, port: int, pid: int):
    """Starts up threads to listen for incoming messages and user input"""
    port_listener = threading.Thread(target = listener, args = [ip, port])
    port_listener.start()
    consumer_thread = threading.Thread(target = consumer, args = [pid])
    consumer_thread.start()
    transaction_enqueue_thread = threading.Thread(target = transaction_enqueue)
    transaction_enqueue_thread.start()
    user_input()

def user_input():
    transaction_re = re.compile(r'moneyTransfer\((\d+), (\d+), (\d+)\)')
    fail_link_re = re.compile(r'failLink\((\d+)\)')
    fix_link_re = re.compile(r'fixLink\((\d+)\)')
    while True:
        user_input = input()
        transaction_event = transaction_re.match(user_input)
        fail_link_event = fail_link_re.match(user_input)
        fix_link_event = fix_link_re.match(user_input)
        if user_input == 'print blockchain':
            print(blockchain)
            logger.info('depth of blockchain: %s', blockchain.depth)
        elif user_input == 'print balance':
            print(f'balance: {balance}')
        elif transaction_event:
            logger.debug("transaction initiated")
            sender = int(transaction_event.group(1))
            receiver = int(transaction_event.group(2))
            amount = int(transaction_event.group(3))
            logger.info("adding transaction with sender: %s, receiver: %s, amount: %s", sender, receiver, amount)
            pending_transaction_queue.put(sender, receiver, amount)
        elif fail_link_event:
            dest = int(fail_link_event.group(1))
            logger.debug("failing link from %d to %d", pid, dest)
            link_status[dest] = False
        elif fix_link_event:
            dest = int(fix_link_event.group(1))
            logger.debug("fixing link from %d to %d", pid, dest)
            link_status[dest] = True
            
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
        msg = pickle.loads(conn.recv(1024))
        logger.debug("received event from %s", addr)
        if isinstance(msg, message) and link_status[msg.sender]:
            event_queue.put(msg.event)

def transaction_enqueue():
    logger.debug("transaction enqueuer started")
    while True:
        if not pending_transaction_queue.empty():
            logger.debug("starting leader election due to new transaction")
            event_queue.put(start_paxos("begin"))
            time.sleep(60)
        

def send_event(event, destination: int):
    logger.debug("sending message to client %s", destination)
    msg = message(pid, destination, event)
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((ip, port_mapping[destination]))
            sock.send(pickle.dumps(msg))
    except (socket.error, socket.gaierror):
        logger.debug("failed to send message")

        
def consumer(pid: int):
    global acceptVal
    while True:
        event = event_queue.get(True, None)
        logger.debug("Processing event of type: %s", type(event))
        if isinstance(event, start_paxos):
            start_paxos_handler(event)
        if isinstance(event, proposal):
            proposal_handler(event)
        elif isinstance(event, promise):
            promise_handler(event)
        elif isinstance(event, accept):
            accept_handler(event)
        elif isinstance(event, accepted):
            accepted_handler(event)
        elif isinstance(event, decision):
            append_block(event.value)
            acceptVal = None
        elif isinstance(event, stale):
            stale_handler(event)
        elif isinstance(event, request):
            request_handler
            
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

# TODO: spawn thread to prevent this from being blocking
def compute_block() -> node:
    transactions = []
    while not pending_transaction_queue.empty():
        transaction = pending_transaction_queue.get()
        logger.debug("pending transaction: %s", transaction)
        transactions.append(transaction)
    logger.debug("About to compute block with transactions: %s", transactions)
    block = node(transactions)
    logger.debug("computed a new block")
    logger.debug("%s", block)
    return block

def append_block(block : node):
    logger.debug("adding a new block to blockchain")
    logger.debug("%s", block)
    blockchain.addNode(block)

def start_paxos_handler(event: start_paxos):
    global ballotNum
    global pid
    ballotNum = ballot(ballotNum.ballotNum + 1, pid, blockchain.depth + 1)
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


def proposal_handler(event: proposal):
    global ballotNum
    global pid
    if event.ballot.depth == blockchain.depth + 1 and event.ballot >= ballotNum:
        ballotNum = event.ballot
        sender = threading.Thread(target = send_event, args = [
                promise(event.ballot, acceptNum, acceptVal),
                event.ballot.proposer
            ])
        sender.start()
    elif event.ballot.depth <= blockchain.depth:
        #TODO send stale blockchain message
        # send missing nodes
        pass
    elif event.ballot.depth > blockchain.depth + 1:
        #TODO update blockchain by requesting from sender
        #Accept proposal
        pass

def accepted_handler(event: accepted):
    global pid
    acceptedBals[event.ballot] += 1
    if acceptedBals[event.ballot] == 2:
        for process in range (1, 6):
            if process != pid:
                sender = threading.Thread(target= send_event, args = [
                    decision(ballotNum, current_transaction),
                    process
                ])
                sender.start()
        blockchain.addNode(current_transaction)

def promise_handler(event: promise):
    global pid
    global current_transaction
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


def accept_handler(event: accept):
    global pid
    global acceptNum
    global acceptVal
    if event.ballot.depth == blockchain.depth + 1 and event.ballot >= ballotNum:
        acceptNum = event.ballot
        acceptVal = event.myVal
        sender = threading.Thread(target= send_event, args = [
            accepted(event.ballot, event.myVal), event.ballot.proposer
        ])
        sender.start()
    elif event.ballot.depth <= blockchain.depth:
        #TODO send stale blockchain message
        pass
    elif event.ballot.depth > blockchain.depth + 1:
        #TODO update blockchain by requesting from sender
        #Accept proposal
        pass

def stale_handler(event : stale):
    global blockchain
    global ballotNum
    blockchain = blockchain()
    while event.blocks:
        blockchain.addNode(event.blocks.pop(-1))
    ballotNum = (max(event.ballotNum.ballotNum), pid, blockchain.depth)

def request_handler(event : request):
    sender = threading.Thread(target= send_event, args = [
        stale(ballotNum, blockchain),
        event.requester
    ])
    sender.start()


def main(argv):
    if len(argv) == 1:
        logger.critical("No command line argument: missing client number")
        return
    configure(int(argv[1]))
    
if __name__ == "__main__":
    main(sys.argv)