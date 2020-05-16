from dataclasses import dataclass
from transaction import transaction
from ballot import ballot

@dataclass
class promise:
    ballot : ballot
    acceptNum : int
    acceptVal : transaction