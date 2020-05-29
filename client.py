import logging
import re
import sys
import socket
import threading
import pickle
import time
import random
from queue import Queue
import pathlib

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
from collections import deque
from save_state import save_state

logging.basicConfig(format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

port_mapping = {}
link_status = {}
ip = None
event_queue = Queue()
pending_transaction_queue = deque()
ballotMap = {}
acceptedBals = {}
block_chain = blockchain()
ballotNum = ballot(0, 0, 0)
acceptNum = ballot(0, 0, 0)
acceptVal = None
current_transaction = None
balance = 100
pending_credit = 0
pid = 0
current_block = None
finished_paxos = True
# TODO: add some fricking locks 

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

def initialize(ip: str, port: int, pid: int):
    """Starts up threads to listen for incoming messages and user input"""
    restore_state()
    port_listener = threading.Thread(target = listener, args = [ip, port])
    port_listener.daemon = True
    port_listener.start()
    consumer_thread = threading.Thread(target = consumer, args = [pid])
    consumer_thread.daemon = True
    consumer_thread.start()
    transaction_enqueue_thread = threading.Thread(target = transaction_enqueue)
    transaction_enqueue_thread.daemon = True
    transaction_enqueue_thread.start()
    if current_block:
        logger.debug("restarting paxos due to current block in save state")
        event_queue.put(start_paxos("begin"))
    user_input()
    

def user_input():
    global link_status
    global pending_transaction_queue
    global balance
    global block_chain
    global pending_credit
    transaction_re = re.compile(r'moneyTransfer\((\d+), (\d+), (\d+)\)')
    fail_link_re = re.compile(r'failLink\((\d+)\)')
    fix_link_re = re.compile(r'fixLink\((\d+)\)')
    while True:
        user_input = input()
        transaction_event = transaction_re.match(user_input)
        fail_link_event = fail_link_re.match(user_input)
        fix_link_event = fix_link_re.match(user_input)
        if user_input == 'print blockchain':
            print(block_chain)
            logger.info('depth of blockchain: %s', block_chain.depth)
        elif user_input == 'print balance':
            print(f'balance: {balance}')
        elif user_input == 'failProcess' or user_input == 'exit':
            save_process()
            break
        elif transaction_event:
            logger.debug("transaction initiated")
            sender = int(transaction_event.group(1))
            receiver = int(transaction_event.group(2))
            amount = int(transaction_event.group(3))
            pending_credit += amount
            if not balance - pending_credit < 0:        
                logger.info("adding transaction with sender: %s, receiver: %s, amount: %s", sender, receiver, amount)
                pending_transaction_queue.append(transaction(sender, receiver, amount))
            else:
                print("failed to initiate transaction: spending too much")
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
    global link_status
    with conn:
        msg = pickle.loads(conn.recv(1024))
        logger.debug("received event from %s", addr)
        if isinstance(msg, message) and link_status[msg.sender]:
            event_queue.put(msg.event)

def transaction_enqueue():
    global finished_paxos
    logger.debug("transaction enqueuer started")
    while True:
        if len(pending_transaction_queue) != 0 and finished_paxos:
            finished_paxos = False
            time.sleep(random.randint(3, 7))
            logger.debug("starting leader election due to new transaction")
            event_queue.put(start_paxos("begin"))

        

def send_event(event, destination: int):
    time.sleep(3)
    global link_status
    msg = message(pid, destination, event)
    if link_status[destination]:
        logger.debug("sending message to client %s", destination)
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((ip, port_mapping[destination]))
                sock.send(pickle.dumps(msg))
        except (socket.error, socket.gaierror):
            logger.debug("failed to send message")

        
def consumer(pid: int):
    global acceptVal
    global current_block
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
            request_handler(event)
            
def timeout_proposal(ballotNum):
    global ballotMap
    time.sleep(15)
    if len(ballotMap[ballotNum]) < 2:
        event_queue.put(start_paxos("begin"))


def timeout_acceptance(ballotNum):
    global acceptedBals
    time.sleep(15)
    if acceptedBals[ballotNum] < 2:
        event_queue.put(start_paxos("begin"))

def compute_block() -> node:
    global current_block
    global block_chain
    transactions = []
    if current_block:
        transactions = current_block.transactions
        current_block = None
    while pending_transaction_queue:
        transaction = pending_transaction_queue.pop()
        logger.debug("pending transaction: %s", transaction)
        transactions.append(transaction)
    logger.debug("About to compute block with transactions: %s", transactions)
    block = node(transactions, ballotNum, block_chain.tail)
    logger.debug("computed a new block")
    logger.debug("%s", block)
    current_block = block
    return block

def append_block(block : node):
    global current_block
    global pending_credit
    global balance
    logger.debug("adding a new block to blockchain")
    logger.debug("%s", block)
    if current_block and block == current_block:
        current_block = None
    block_chain.addNode(block)
    for t in block.transactions:
        if t.sender == pid:
            pending_credit -= t.amount
            balance -= t.amount
        if t.receiver == pid:
            balance += t.amount

def start_paxos_handler(event: start_paxos):
    global ballotNum
    global pid
    ballotNum = ballot(ballotNum.ballotNum + 1, pid, block_chain.depth + 1)
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
    if event.ballot.depth == block_chain.depth + 1 and event.ballot >= ballotNum:
        ballotNum = event.ballot
        sender = threading.Thread(target = send_event, args = [
                promise(event.ballot, acceptNum, acceptVal),
                event.ballot.proposer
            ])
        sender.start()
    elif event.ballot.depth <= block_chain.depth:
        logger.debug("sender was out of date, sending them a stale message")
        sender = threading.Thread(target= send_event, args=[
            stale(ballotNum, block_chain),
            event.ballot.proposer
        ])
        sender.start()
    elif event.ballot.depth > block_chain.depth + 1:
        logger.debug("out of date: sending request")
        requester = threading.Thread(target= send_event, args=[
            request(ballotNum, pid),
            event.ballot.proposer
        ])
        requester.start()

def accepted_handler(event: accepted):
    global pid
    global finished_paxos
    acceptedBals[event.ballot] += 1
    if acceptedBals[event.ballot] == 2:
        for process in range (1, 6):
            if process != pid:
                sender = threading.Thread(target= send_event, args = [
                    decision(ballotNum, current_transaction),
                    process
                ])
                sender.start()
        append_block(current_transaction)
        finished_paxos = True

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
    if event.ballot.depth == block_chain.depth + 1 and event.ballot >= ballotNum:
        acceptNum = event.ballot
        acceptVal = event.myVal
        sender = threading.Thread(target= send_event, args = [
            accepted(event.ballot, event.myVal), event.ballot.proposer
        ])
        sender.start()
    elif event.ballot.depth <= block_chain.depth:
        logger.debug("sender was out of date, sending them a stale message")
        sender = threading.Thread(target= send_event, args=[
            stale(ballotNum, block_chain),
            event.ballot.proposer
        ])
        sender.start()
    elif event.ballot.depth > block_chain.depth + 1:
        logger.debug("out of date: sending request")
        requester = threading.Thread(target= send_event, args=[
            request(ballotNum, pid),
            event.ballot.proposer
        ])
        requester.start()
        

def stale_handler(event : stale):
    global block_chain
    global ballotNum
    global balance
    balance = 100
    block_chain = blockchain()
    while event.blocks:
        block = event.blocks.pop(-1)
        append_block(block)
    ballotNum = ballot(event.ballotNum.ballotNum, pid, block_chain.depth)

def request_handler(event : request):
    logger.debug("received a request from %s", event.requester)
    sender = threading.Thread(target= send_event, args = [
        stale(ballotNum, block_chain),
        event.requester
    ])
    sender.start()

def save_process():
    global pending_transaction_queue
    global current_block
    global block_chain
    global pid
    logger.debug("saving ")
    saved_client = save_state(pending_transaction_queue, current_block,
                                block_chain)
    with open(f'client_{pid}.data', 'w+b') as save_file:
        pickle.dump(saved_client, save_file)

def restore_state():
    global pending_transaction_queue
    global current_block
    global block_chain
    path = pathlib.Path(f'client_{pid}.data')
    if path.exists():
        with open(path, 'rb') as save_file:
            save_state = pickle.load(save_file)
            pending_transaction_queue = save_state.pending_transaction_queue
            current_block = save_state.current_block
            block_chain = save_state.block_chain
    

def main(argv):
    if len(argv) == 1:
        logger.critical("No command line argument: missing client number")
        return
    configure(int(argv[1]))
    
if __name__ == "__main__":
    main(sys.argv)