from dataclasses import dataclass
from dataclasses import field

@dataclass(unsafe_hash=True, order=True, eq=True)
class ballot:
    ballotNum : int
    proposer : int
    depth : int


    def __str__(self):
        return f"(ballotNum: {self.ballotNum}, proposer: {self.proposer}, depth: {self.depth})"

    def __repr__(self):
        return f"(ballotNum: {self.ballotNum}, proposer: {self.proposer}, depth: {self.depth})"