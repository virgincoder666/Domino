
from typing import List, Optional, Tuple
import random
from .models import Dom, Move, normalize, all_double6
from .rules import legal_moves, apply_move
from .belief import Belief
from .ai import choose_move

TEAM_A = {0,2}
TEAM_B = {1,3}

class Game:
    def __init__(self, rng: Optional[random.Random]=None):
        self.rng = rng or random.Random()
        self.reset_scores()

    def reset_scores(self):
        self.scores = [0,0]
        self.first_round = True
        self.next_starter: Optional[int] = None  # quién abre la siguiente ronda

    def deal_round(self):
        tiles = all_double6()
        self.rng.shuffle(tiles)
        self.hands = [sorted(tiles[i*7:(i+1)*7]) for i in range(4)]
        self.chain: List[Dom] = []
        self.passes_in_row = 0
        self.belief = Belief(players=4)
        self.belief.init_with(all_double6(), self.hands, me=-1)

        if self.first_round:
            # Abre quien tenga el doble más alto; JUEGA esa ficha y pasa el turno a su derecha
            for d in [(6,6),(5,5),(4,4),(3,3),(2,2),(1,1),(0,0)]:
                for pid in range(4):
                    if d in self.hands[pid]:
                        self.first_player = pid
                        self.chain = [d]
                        # remover (normalizado) de la mano del que abre
                        tgt = normalize(d)
                        for i, dd in enumerate(self.hands[pid]):
                            if normalize(dd) == tgt:
                                del self.hands[pid][i]
                                break
                        self.belief.mark_played(d, pid)
                        # pasa el turno al siguiente jugador (a su derecha)
                        self.current = (pid + 1) % 4
                        return
            # en práctica no se llega aquí
        else:
            # Abre el jugador ya decidido por la ronda anterior; NO se juega automáticamente
            starter = self.next_starter if self.next_starter is not None else 0
            self.first_player = starter
            self.current = starter
            # cadena vacía -> el abridor podrá jugar cualquier ficha (OPEN)

    def ends(self) -> Tuple[int,int]:
        if not self.chain: return (-1,-1)
        return (self.chain[0][0], self.chain[-1][1])

    def team_index(self, pid: int) -> int:
        return 0 if pid in TEAM_A else 1

    def hands_sizes(self) -> List[int]:
        return [len(h) for h in self.hands]

    def _remove_from_hand_norm(self, pid: int, dom: Dom):
        tgt = normalize(dom)
        hand = self.hands[pid]
        for i, d in enumerate(hand):
            if normalize(d) == tgt:
                del hand[i]
                return True
        return False

    def step_ai(self):
        pid = self.current
        hand = self.hands[pid]
        moves = legal_moves(self.chain, hand)
        if not moves:
            L,R = self.ends()
            if L!=-1:
                self.belief.mark_pass(pid, L, R)
            self.passes_in_row += 1
            self.current = (self.current + 1) % 4
            return None
        mv = choose_move(pid, hand, self.chain, self.belief, self.hands_sizes())
        self.chain = apply_move(self.chain, mv)
        self._remove_from_hand_norm(pid, mv.dom)
        self.belief.mark_played(mv.dom, pid)
        self.passes_in_row = 0
        self.current = (self.current + 1) % 4
        return mv

    def round_over(self) -> bool:
        if any(len(h)==0 for h in self.hands):
            return True
        if self.passes_in_row >= 4:
            return True
        return False

    def round_score(self) -> Tuple[int,int]:
        """Calcula puntos y además fija quién abre la PRÓXIMA ronda.
        Regresa (puntosA, puntosB)."""
        sums = [sum(a+b for a,b in h) for h in self.hands]
        empties = [i for i,h in enumerate(self.hands) if len(h)==0]

        winner_player: Optional[int] = None
        winner_team: Optional[int] = None

        if len(empties)>0:
            winner_player = empties[0]
            winner_team = self.team_index(winner_player)
            # puntaje: suma del equipo perdedor
            if winner_team == 0:
                scoreA, scoreB = 0, sums[1] + sums[3]
            else:
                scoreA, scoreB = sums[0] + sums[2], 0
        else:
            # Bloqueo: gana el equipo con menor suma
            sumA = sums[0] + sums[2]
            sumB = sums[1] + sums[3]
            if sumA < sumB:
                winner_team = 0
                scoreA, scoreB = (sumB - sumA), 0
            elif sumB < sumA:
                winner_team = 1
                scoreA, scoreB = 0, (sumA - sumB)
            else:
                winner_team = None  # empate real (poco común)
                scoreA, scoreB = 0, 0

        # Decidir abridor de la próxima ronda
        if winner_player is not None:
            self.next_starter = winner_player
        elif winner_team is not None:
            # escoger del equipo ganador el jugador con menor suma de pips
            candidates = [0,2] if winner_team==0 else [1,3]
            sums_players = {pid: sums[pid] for pid in candidates}
            self.next_starter = min(sums_players, key=sums_players.get)
        else:
            # empate: rotamos al siguiente de quien fue first_player
            self.next_starter = (self.first_player + 1) % 4

        self.first_round = False  # a partir de ahora ya no se abre con doble seis
        return (scoreA, scoreB)
