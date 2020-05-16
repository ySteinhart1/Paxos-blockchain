from dataclasses import dataclass
from transaction import transaction
from ballot import ballot

@dataclass
class accept:
    ballot : ballot
    myVal : transaction