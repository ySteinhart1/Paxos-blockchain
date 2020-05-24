from transaction import transaction
from hashlib import sha256
import random
import string

class node:
    def __init__(self, transactions, prev=None):
        self.transactions = transactions
        prevContents = ""
        if prev:
            prevContents += str(prev.transactions)
            prevContents += self.prev.nonce
            prevContents += self.prev.hash
        self.hash = sha256(prevContents)
        self.nonce = calculateNonce()

    def calculateNonce(self):
        nonce = ''.join([random.choice(string.ascii_letters + string.digits) for _ in range(16)])
        transactionStr = str(self.transactions)
        while int(sha256(transactionStr + nonce)[-1]) > 4:
            nonce = ''.join([random.choice(string.ascii_letters + string.digits) for _ in range(16)])
        return nonce



class blockchain:
    def __init__(self):
        self.tail = None
        self.depth = 0

    def addNode(self, node: node) {
        if self.tail:
            node.prev = self.tail
        self.tail = node
        self.depth += 1
    }