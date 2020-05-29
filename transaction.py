from dataclasses import dataclass

@dataclass
class transaction:
    sender: int
    receiver: int
    amount: int

    def __repr__(self):
        return f"{{sender: {self.sender}, receiver: {self.receiver}, amount: {self.amount}}}"
    
    def __str__(self):
        return f"{{sender: {self.sender}, receiver: {self.receiver}, amount: {self.amount}}}"