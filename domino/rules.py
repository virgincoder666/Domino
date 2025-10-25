
from typing import List
from .models import Dom, Move

def can_play_on(end: int, d: Dom) -> bool:
    a, b = d
    return a == end or b == end

# Para JUGAR A LA IZQUIERDA (L): queremos que b == L
def orient_for_left(L: int, d: Dom) -> Dom:
    a, b = d
    return (a, b) if b == L else (b, a)

# Para JUGAR A LA DERECHA (R): queremos que a == R
def orient_for_right(R: int, d: Dom) -> Dom:
    a, b = d
    return (a, b) if a == R else (b, a)

def legal_moves(chain: List[Dom], hand: List[Dom]) -> List[Move]:
    if not chain:
        return [Move(d, "OPEN") for d in hand]

    L = chain[0][0]
    R = chain[-1][1]
    moves: List[Move] = []

    for d in hand:
        if can_play_on(L, d):
            moves.append(Move(orient_for_left(L, d), "L"))
        if can_play_on(R, d):
            moves.append(Move(orient_for_right(R, d), "R"))

    return moves

def apply_move(chain: List[Dom], mv) -> List[Dom]:
    """Inserta la ficha orientándola correctamente según el lado elegido."""
    d = mv.dom
    if not chain:
        # mesa vacía: poner tal cual
        return [d]

    L = chain[0][0]     # extremo izquierdo actual
    R = chain[-1][1]    # extremo derecho actual
    a, b = d

    if mv.side == 'L':
        # El valor que toque L debe quedar en la "derecha" de la ficha insertada (b == L)
        if b == L:
            return [d] + chain
        elif a == L:
            return [(b, a)] + chain
    elif mv.side == 'R':
        # El valor que toque R debe quedar en la "izquierda" de la ficha insertada (a == R)
        if a == R:
            return chain + [d]
        elif b == R:
            return chain + [(b, a)]

    # Si cae aquí es un movimiento inválido
    raise ValueError(f"Movimiento inválido: dom={d}, side={mv.side}, ends={(L,R)}")
