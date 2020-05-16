from dataclasses import dataclass
import transaction
import ballot

@dataclass
class promise:
    ballot : ballot
    acceptNum : int
    acceptVal : transaction