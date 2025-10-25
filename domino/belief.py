
from typing import Dict, List, Set
from .models import Dom, normalize

class Belief:
    def __init__(self, players: int = 4):
        self.players = players
        self.possible: Dict[Dom, Set[int]] = {}
        self.unseen: Set[Dom] = set()

    def init_with(self, all_tiles: List[Dom], hands: List[List[Dom]], me: int):
        self.unseen = set(normalize(d) for d in all_tiles)
        self.possible = {normalize(d): set(range(self.players)) for d in all_tiles}
        for pid, hand in enumerate(hands):
            for d in hand:
                nd = normalize(d)
                self.unseen.discard(nd)
                self.possible[nd] = {pid}

    def mark_played(self, d: Dom, by: int):
        nd = normalize(d)
        self.possible[nd] = {by}
        self.unseen.discard(nd)

    def mark_pass(self, player_id: int, left_end: int, right_end: int):
        for d in list(self.unseen):
            a, b = d
            if a == left_end or b == left_end or a == right_end or b == right_end:
                self.possible[d].discard(player_id)

    def prob_owner(self, d: Dom, pid: int, hands_sizes: List[int]) -> float:
        s = self.possible.get(normalize(d), set())
        if pid not in s:
            return 0.0
        return 1.0 / max(1, len(s))
