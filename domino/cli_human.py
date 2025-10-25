
from typing import List
from .game import Game
from .rules import legal_moves, apply_move
from .models import normalize

def remove_from_hand_norm(hand: List[tuple], dom: tuple):
    tgt = normalize(dom)
    for i, d in enumerate(hand):
        if normalize(d) == tgt:
            del hand[i]
            return True
    return False

def pick_move_input(moves: list, chain: list):
    print(f"Mesa: {chain}")
    print("Tus jugadas legales:")
    for i, mv in enumerate(moves):
        print(f"  [{i}] ficha={mv.dom} lado={mv.side}")
    while True:
        try:
            sel = int(input("Elige el índice de la jugada (o -1 para pasar): "))
            if sel == -1:
                return None
            if 0 <= sel < len(moves):
                return moves[sel]
        except Exception:
            pass
        print("Entrada inválida. Intenta de nuevo.")

def play_match():
    g = Game()
    g.reset_scores()
    while g.scores[0] < 100 and g.scores[1] < 100:
        g.deal_round()
        print(f"\n--- Nueva ronda. Empieza J{g.first_player} ---")
        print(f"Tu mano (J0): {g.hands[0]}")
        while not g.round_over():
            pid = g.current
            if pid == 0:
                moves = legal_moves(g.chain, g.hands[0])
                if not moves:
                    print("No puedes jugar. PASAS.")
                    L,R = g.ends()
                    if L != -1:
                        g.belief.mark_pass(0, L, R)
                    g.passes_in_row += 1
                    g.current = (g.current + 1) % 4
                else:
                    mv = pick_move_input(moves, g.chain)
                    if mv is None:
                        L,R = g.ends()
                        if L != -1:
                            g.belief.mark_pass(0, L, R)
                        g.passes_in_row += 1
                        g.current = (g.current + 1) % 4
                    else:
                        g.chain = apply_move(g.chain, mv)
                        remove_from_hand_norm(g.hands[0], mv.dom)
                        g.belief.mark_played(mv.dom, 0)
                        g.passes_in_row = 0
                        g.current = (g.current + 1) % 4
            else:
                mv = g.step_ai()
                pid_played = (g.current - 1) % 4
                if mv is None:
                    print(f"J{pid_played} pasa. Mesa: {g.chain} Extremos:{g.ends()}")
                else:
                    print(f"J{pid_played} juega {mv.dom} {mv.side}. Mesa: {g.chain}")
        a,b = g.round_score()
        print(f"Ronda termina. A+{a}  B+{b}. Marcador: A={g.scores[0]+a} B={g.scores[1]+b}")
        g.scores[0] += a
        g.scores[1] += b
    ganador = "Equipo A" if g.scores[0] >= 100 else "Equipo B"
    print("=== PARTIDA TERMINA ===")
    print("Ganador:", ganador)

if __name__ == '__main__':
    play_match()
