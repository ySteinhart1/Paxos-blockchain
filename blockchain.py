from transaction import transaction
from ballot import ballot
from hashlib import sha256
import random
import string

class node:
    prev = None
    def __init__(self, transactions, ballotNum, prev=None):
        self.transactions = transactions
        prevContents = ""
        self.ballotNum = ballotNum
        if prev:
            prevContents += str(prev.transactions)
            prevContents += prev.nonce
            prevContents += prev.hash
        self.hash = sha256(prevContents.encode('utf-8')).hexdigest()
        self.nonce = self.calculateNonce()

    def calculateNonce(self):
        nonce = ''.join([random.choice(string.ascii_letters + string.digits) for _ in range(16)])
        transactionStr = str(self.transactions)
        while int((sha256((transactionStr + nonce + self.hash).encode('utf-8')).hexdigest()), 16) % 16 > 4:
            nonce = ''.join([random.choice(string.ascii_letters + string.digits) for _ in range(16)])
        return nonce

    def __repr__(self):
        return f"{{transactions: {str(self.transactions)}, nonce: {self.nonce}, hash: {self.hash}}}"

    def __str__(self):
        return f"{{transactions: {str(self.transactions)}, nonce: {self.nonce}, hash: {self.hash}}}"
    
    def __eq__(self, value):
        return (self.transactions == value.transactions) and (self.ballotNum == value.ballotNum)




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
            blockString = f"{{transactions: {n.transactions}, nonce: {n.nonce}, hash: {n.hash}}}\n" + blockString
            n = n.prev
        return blockString

    def __str__(self):
        blockString = ""
        n = self.tail
        while n:
            blockString = f"{{transactions: {n.transactions}, nonce: {n.nonce}, hash: {n.hash}}}\n" + blockString
            n = n.prev
        return blockString

