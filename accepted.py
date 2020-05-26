from dataclasses import dataclass
from transaction import transaction
from ballot import ballot
from blockchain import node

@dataclass
class accepted:
    ballot : ballot
    value : node