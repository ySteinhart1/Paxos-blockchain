from dataclasses import dataclass

@dataclass(unsafe_hash=True, order=True, eq=True)
class ballot:
    ballotNum : int
    proposer : int
    depth : int = field(order=False)
