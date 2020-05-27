from dataclasses import dataclasses
from ballot import ballot

@dataclasses
class request:
    ballot : ballot
    requester : int