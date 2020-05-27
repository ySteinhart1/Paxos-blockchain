from dataclasses import dataclass
import typing

@dataclass
class message:
    sender: int
    receiver: int
    event: typing.Any