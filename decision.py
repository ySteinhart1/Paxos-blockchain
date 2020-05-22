from dataclasses import dataclass
from transaction import transaction
from ballot import ballot

@dataclass
class decision:
    ballot: ballot
    value : transaction