from transaction import transaction
from hashlib import sha256
import random
import string

class node:
    prev = None
    def __init__(self, transactions, prev=None):
        self.transactions = transactions
        prevContents = ""
        if prev:
            prevContents += str(prev.transactions)
            prevContents += self.prev.nonce
            prevContents += self.prev.hash
        self.hash = sha256(prevContents.encode('utf-8')).hexdigest()
        self.nonce = self.calculateNonce()

    def calculateNonce(self):
        nonce = ''.join([random.choice(string.ascii_letters + string.digits) for _ in range(16)])
        transactionStr = str(self.transactions)
        while int((sha256((transactionStr + nonce).encode('utf-8')).hexdigest()), 16) % 10 > 4:
            nonce = ''.join([random.choice(string.ascii_letters + string.digits) for _ in range(16)])
        return nonce

    def __repr__(self):
        return f"{{transactions: {self.transactions}, nonce: {self.nonce}, hash: {self.hash}}}"

    def __str__(self):
        return f"{{transactions: {self.transactions}, nonce: {self.nonce}, hash: {self.hash}}}"




class blockchain:
    def __init__(self):
        self.tail = None
        self.depth = 0

    def addNode(self, node: node):
        if self.tail:
            node.prev = self.tail
        self.tail = node
        self.depth += 1
    

    def __repr__(self):
        blockString = ""
        n = self.tail
        while n:
            blockString = f"{{transactions: {n.transactions}, nonce: {n.nonce}, hash: {n.hash}}}" + blockString
            n = n.prev
        return blockString

    def __str__(self):
        blockString = ""
        n = self.tail
        while n:
            blockString = f"{{transactions: {n.transactions}, nonce: {n.nonce}, hash: {n.hash}}}" + blockString
            n = n.prev
        return blockString

