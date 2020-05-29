from dataclasses import dataclass
from ballot import ballot

@dataclass
class request:
    ballot : ballot
    requester : int