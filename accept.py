from dataclasses import dataclass
import transaction
import ballot

@dataclass
class accept:
    ballot : ballot
    myVal : transaction