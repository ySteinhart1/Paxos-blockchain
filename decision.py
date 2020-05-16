from dataclasses import dataclass
from transaction import transaction

@dataclass
class decision:
    ballot: ballot
    value : transaction