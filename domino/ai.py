
from typing import List
from collections import Counter
from .models import Dom, Move
from .rules import legal_moves
from .belief import Belief

def numbers_in_hand(hand: List[Dom]) -> Counter:
    c = Counter()
    for a,b in hand:
        c[a]+=1; c[b]+=1
    return c

def estimate_play_prob(end: int, opponent_id: int, belief: Belief, hands_sizes: List[int]) -> float:
    tiles = list({(min(end, k), max(end, k)) for k in range(7)})
    p_no = 1.0
    for d in tiles:
        p_has = belief.prob_owner(d, opponent_id, hands_sizes)
        p_no *= (1.0 - p_has)
    return 1.0 - p_no

def score_move(move: Move, hand_after: List[Dom], chain_after: List[Dom],
               player_id: int, belief: Belief, hands_sizes: List[int]) -> float:
    L = chain_after[0][0]
    R = chain_after[-1][1]
    cnt = numbers_in_hand(hand_after)
    control = cnt[L] + cnt[R]
    opp = (player_id + 1) % 4
    pL = estimate_play_prob(L, opp, belief, hands_sizes)
    pR = estimate_play_prob(R, opp, belief, hands_sizes)
    anti_gift = 1.0 - max(pL, pR)
    a,b = move.dom
    double_bonus = 0.5 if a==b else 0.0
    diversity = len([x for x in range(7) if cnt[x]>0])
    return 1.4*control + 1.2*anti_gift + 0.5*double_bonus + 0.3*diversity

def choose_move(player_id: int, hand: List[Dom], chain: List[Dom],
                belief: Belief, hands_sizes: List[int]) -> Move:
    moves = legal_moves(chain, hand)
    best = None
    best_score = -1e9
    for mv in moves:
        chain_after = [mv.dom] if mv.side=='OPEN' else ([mv.dom]+chain if mv.side=='L' else chain+[mv.dom])
        hand_after = [d for d in hand if d != mv.dom]
        s = score_move(mv, hand_after, chain_after, player_id, belief, hands_sizes)
        if s > best_score:
            best_score = s
            best = mv
    return best
