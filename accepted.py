from dataclasses import dataclass
from transaction import transaction
from ballot import ballot

@dataclass
class accepted:
    ballot : ballot
    value : transaction