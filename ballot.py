from dataclasses import dataclass
from dataclasses import field

@dataclass(unsafe_hash=True, order=True, eq=True)
class ballot:
    ballotNum : int
    proposer : int
    depth : int
