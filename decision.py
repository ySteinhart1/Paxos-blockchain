from dataclasses import dataclass
from transaction import transaction
from ballot import ballot
from blockchain import node

@dataclass
class decision:
    ballot: ballot
    value : node