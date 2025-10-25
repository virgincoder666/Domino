
from dataclasses import dataclass
from typing import List, Tuple

Dom = Tuple[int, int]

def normalize(dom: Dom) -> Dom:
    a, b = dom
    return (a, b) if a <= b else (b, a)

def all_double6() -> List[Dom]:
    s = []
    for a in range(7):
        for b in range(a, 7):
            s.append((a, b))
    return s

def pip_sum(hand: List[Dom]) -> int:
    return sum(a + b for a, b in hand)

@dataclass
class Move:
    dom: Dom
    side: str  # 'L' o 'R' o 'OPEN' (solo en la primera jugada)
