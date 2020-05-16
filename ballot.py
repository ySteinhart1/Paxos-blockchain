from dataclasses import dataclass

@dataclass
class ballot:
    ballotNum : int
    proposer : int

    def __eq__(self, value):
        return (self.ballotNum == value.ballotNum and self.proposer == value.proposer)

    def __lt__(self, value):
        if self.ballotNum < value.ballotNum:
            return True
        else:
            return self.proposer < value.proposer