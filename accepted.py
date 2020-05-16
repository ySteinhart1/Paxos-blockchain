from dataclasses import dataclass
import transaction
import ballot

@dataclass
class accepted:
    ballot : ballot
    value : transaction