from dataclasses import dataclass

@dataclass
class transaction:
    sender: int
    receiver: int
    amount: int

    def __repr__(self):
        return f"{{sender: {sender}, receiver: {receiver}, amount: {amount}}}"
    
    def __str__(self):
        return f"{{sender: {sender}, receiver: {receiver}, amount: {amount}}}"