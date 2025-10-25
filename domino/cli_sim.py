
from .game import Game

if __name__ == "__main__":
    g = Game()
    # Simple loop to 100 (console)
    while g.scores[0] < 100 and g.scores[1] < 100:
        g.deal_round()
        while not g.round_over():
            g.step_ai()
        a,b = g.round_score()
        g.scores[0] += a; g.scores[1] += b
        print(f"Ronda termina. A+{a}  B+{b}  => Marcador A={g.scores[0]} B={g.scores[1]}")
    print("Ganador:", "Equipo A" if g.scores[0] >= 100 else "Equipo B")
