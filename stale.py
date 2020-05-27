from dataclasses import dataclasses
from blockchain import blockchain, node
from ballot import ballot
from typing import List

@dataclasses
class stale:
    ballotNum : ballot
    blocks : List[node]


    def __init__(self, ballotNum, blockchain):
        self.ballotNum = ballotNum
        self.blocks = []
        n = blockchain.tail
        while n:
            self.blocks.append(n)
            n = n.prev