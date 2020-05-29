from dataclasses import dataclass
from collections import deque
from blockchain import node, blockchain

@dataclass
class save_state:
    pending_transaction_queue: deque
    current_block: node
    block_chain: blockchain