import pygame
from .game import Game
from .rules import legal_moves, apply_move
from .models import normalize
from .ai import estimate_play_prob

WHITE = (240,240,240)
BG = (20,22,26)
GREY = (80,90,100)
BTN = (40,80,60)
ACCENT_A = (80,160,255)
ACCENT_B = (255,120,80)
PANEL = (30,34,40)
HL = (120,180,120)
DARK = (45,50,58)

TILE_W, TILE_H = 72, 40
RENDER_NUMBERS = True   # alterna con tecla N
AI_DELAY_MS = 3000      # ms entre jugadas de bots

# -------------------------------------------------
# util
# -------------------------------------------------
def remove_from_hand_norm(hand, dom):
    tgt = normalize(dom)
    for i, d in enumerate(hand):
        if normalize(d) == tgt:
            del hand[i]
            return True
    return False

def text(surf, txt, x, y, size=24, color=WHITE, font_name='consolas', center=False, bold=True):
    font = pygame.font.SysFont(font_name, size, bold=bold)
    img = font.render(str(txt), True, color)
    rect = img.get_rect()
    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)
    surf.blit(img, rect)

# -------------------------------------------------
# dibujo de fichas
# -------------------------------------------------
def draw_tile(surf, dom, x, y, w=TILE_W, h=TILE_H, color=(60,60,60), rotate90=False):
    """
    Dibuja una ficha horizontal por defecto. Si rotate90=True, la rota 90° (vertical).
    Se dibuja en una superficie temporal y luego se centra en el slot (x,y,w,h).
    """
    a, b = dom

    # superficie temporal horizontal
    tile = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(tile, color, (0, 0, w, h), border_radius=7)
    pygame.draw.line(tile, WHITE, (w // 2, 5), (w // 2, h - 5), 2)  # divisor

    if RENDER_NUMBERS:
        font = pygame.font.SysFont('consolas', max(14, h // 2), bold=True)
        la = font.render(str(a), True, WHITE)
        lb = font.render(str(b), True, WHITE)
        ra = la.get_rect(center=(w // 4, h // 2))
        rb = lb.get_rect(center=(3 * w // 4, h // 2))
        tile.blit(la, ra); tile.blit(lb, rb)
    else:
        # puntos con clip y padding seguro
        PADDING = max(8, min(w, h) // 6)
        inner = pygame.Rect(PADDING, PADDING, w - 2 * PADDING, h - 2 * PADDING)
        prev_clip = tile.get_clip()
        tile.set_clip(inner)

        left_rect  = pygame.Rect(inner.x, inner.y, inner.w // 2, inner.h)
        right_rect = pygame.Rect(inner.x + inner.w // 2, inner.y, inner.w - inner.w // 2, inner.h)
        r = max(2, int(min(left_rect.w, left_rect.h) * 0.10))

        def grid_positions(rect):
            cx = rect.x + rect.w // 2
            cy = rect.y + rect.h // 2
            dx = rect.w // 3 // 2
            dy = rect.h // 3 // 2
            return [
                (rect.x + dx,       rect.y + dy),        (cx,             rect.y + dy),        (rect.right - dx, rect.y + dy),
                (rect.x + dx,       cy),                  (cx,             cy),                  (rect.right - dx, cy),
                (rect.x + dx,       rect.bottom - dy),    (cx,             rect.bottom - dy),    (rect.right - dx, rect.bottom - dy),
            ]

        PAT = {0:[], 1:[4], 2:[0,8], 3:[0,4,8], 4:[0,2,6,8], 5:[0,2,4,6,8], 6:[0,2,3,5,6,8]}

        def draw_side(val, rect):
            grid = grid_positions(rect)
            for idx in PAT.get(val, []):
                gx, gy = grid[idx]
                gx = int(min(max(gx, inner.left + r), inner.right - r))
                gy = int(min(max(gy, inner.top + r),  inner.bottom - r))
                pygame.draw.circle(tile, WHITE, (gx, gy), r)

        draw_side(a, left_rect)
        draw_side(b, right_rect)
        tile.set_clip(prev_clip)

    # rotación y blit centrado en el slot
    if rotate90:
        tile = pygame.transform.rotate(tile, 90)
        rect = tile.get_rect(center=(x + w // 2, y + h // 2))
    else:
        rect = tile.get_rect(topleft=(x, y))
    surf.blit(tile, rect)

def draw_back_tile(surf, x, y, w=TILE_W, h=TILE_H, color=(55,60,70)):
    pygame.draw.rect(surf, color, (x, y, w, h), border_radius=7)
    pygame.draw.rect(surf, (100,110,125), (x+8, y+8, w-16, h-16), width=2, border_radius=6)

def draw_tile_oriented(surf, dom, x, y, prev_right=None, w=TILE_W, h=TILE_H):
    """
    Voltea si hace falta para mantener continuidad.
    Si es MULA (a==b), se dibuja vertical.
    """
    a, b = dom
    rotate90 = (a == b)
    if prev_right is not None and a != prev_right and b == prev_right:
        dom = (b, a)
    draw_tile(surf, dom, x, y, w, h, rotate90=rotate90)

# -------------------------------------------------
# layout serpenteado (curva y baja)
# -------------------------------------------------
def layout_chain_positions(chain, area_rect, tile_w=TILE_W, gap=10):
    """
    Devuelve una lista de (x, y, row_parity). row_parity = 0 para filas izq→der,
    1 para filas der→izq. Sirve para voltear visualmente la ficha en filas impares.
    """
    if not chain:
        return []

    inner_margin = max(12, gap)
    usable_w = max(1, area_rect.width - 2 * inner_margin)

    max_per_row = max(1, (usable_w + gap) // (tile_w + gap))
    n = len(chain)
    rows = (n + max_per_row - 1) // max_per_row

    row_h = max(TILE_H, int(TILE_W * 0.75))
    total_h = rows * row_h
    start_y = area_rect.y + max(0, (area_rect.height - total_h) // 2)

    positions = []
    i = 0
    for r in range(rows):
        count = min(max_per_row, n - i)
        y = start_y + r * row_h

        if r % 2 == 0:
            # izq -> der
            x = area_rect.x + inner_margin
            step = (tile_w + gap)
        else:
            # der -> izq
            x = area_rect.right - inner_margin - tile_w
            step = -(tile_w + gap)

        for _ in range(count):
            positions.append((int(x), int(y), r % 2))
            x += step
            i += 1

    return positions

# -------------------------------------------------
# main
# -------------------------------------------------
def main():
    pygame.init()
    W,H = 1200, 760
    screen = pygame.display.set_mode((W,H))
    pygame.display.set_caption("Dominó 2v2 — Menú + Entrenamiento + Drag & Drop (Mesa)")
    clock = pygame.time.Clock()

    in_menu = True
    training_mode = False
    btn_normal = pygame.Rect(W//2-160, H//2-40, 320, 40)
    btn_training = pygame.Rect(W//2-160, H//2+20, 320, 40)

    g = Game(); g.reset_scores()
    history = []; last_round_points = (0,0)

    def play_new_round():
        nonlocal last_round_points
        g.deal_round()
        last_round_points = (0,0)
        schedule_ai_if_needed()

    selected = None; dragging = False; drag_offset = (0,0); drag_pos = (0,0)
    show_next_round_btn = False; match_over_prompt = False

    tbl_rect = pygame.Rect(20, 160, W-360, 380)
    dropL = pygame.Rect(W//2 - 120, 540, 190, 40)
    dropR = pygame.Rect(W//2 + 80, 540, 190, 40)
    btn_pass = pygame.Rect(W//2 - 70, 590, 140, 34)

    # temporizador bots
    ai_waiting = False
    ai_next_time = 0

    def schedule_ai_if_needed():
        nonlocal ai_waiting, ai_next_time
        if g.current != 0 and not g.round_over():
            ai_waiting = True
            ai_next_time = pygame.time.get_ticks() + AI_DELAY_MS

    running = True
    while running:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False

            if in_menu:
                if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                    mx,my = e.pos
                    if btn_normal.collidepoint(mx,my):
                        training_mode = False; in_menu=False; play_new_round()
                    if btn_training.collidepoint(mx,my):
                        training_mode = True; in_menu=False; play_new_round()
                if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                    running = False
                continue

            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_t:
                    training_mode = not training_mode
                if e.key == pygame.K_n:
                    global RENDER_NUMBERS
                    RENDER_NUMBERS = not RENDER_NUMBERS
                if e.key == pygame.K_ESCAPE:
                    in_menu = True; selected=None; dragging=False
                    ai_waiting = False
                    continue

            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                mx,my = e.pos
                if show_next_round_btn:
                    if 20 <= mx <= 200 and 80 <= my <= 110:
                        show_next_round_btn = False; match_over_prompt=False; play_new_round(); selected=None; dragging=False
                    if 220 <= mx <= 360 and 80 <= my <= 110:
                        running = False
                    continue
                if match_over_prompt:
                    if 20 <= mx <= 240 and 120 <= my <= 150:
                        g.reset_scores(); history.clear(); show_next_round_btn=False; match_over_prompt=False; play_new_round(); selected=None; dragging=False
                    if 260 <= mx <= 400 and 120 <= my <= 150:
                        running = False
                    continue

                # PASAR (solo si no hay jugadas)
                if btn_pass.collidepoint(mx,my) and g.current == 0 and not g.round_over():
                    moves = legal_moves(g.chain, g.hands[0])
                    if not moves:
                        L,R = g.ends()
                        if L != -1:
                            g.belief.mark_pass(0, L, R)
                        g.passes_in_row += 1
                        g.current = (g.current + 1) % 4
                        schedule_ai_if_needed()
                    continue

                # Selección para arrastrar
                base_y = H-110
                for i, d in enumerate(g.hands[0]):
                    x = 20 + i*(TILE_W+8)
                    rect = pygame.Rect(x, base_y, TILE_W, TILE_H)
                    if rect.collidepoint(mx,my):
                        if not legal_moves(g.chain, g.hands[0]) and g.chain:
                            break
                        selected = d; dragging=True
                        drag_offset = (mx - x, my - base_y); drag_pos=(x, base_y)
                        break

            if e.type == pygame.MOUSEMOTION and dragging:
                mx,my = e.pos; drag_pos = (mx - drag_offset[0], my - drag_offset[1])

            if e.type == pygame.MOUSEBUTTONUP and e.button == 1 and dragging:
                mx,my = e.pos
                if not (show_next_round_btn or match_over_prompt):
                    legal = [(mv.side, mv) for mv in legal_moves(g.chain, g.hands[0]) if normalize(mv.dom)==normalize(selected)]
                    sides = {s for s,_ in legal}
                    if dropL.collidepoint(mx,my) and ('L' in sides or 'OPEN' in sides):
                        mv = next((m for s,m in legal if s in ('L','OPEN')), None)
                        if mv:
                            g.chain = apply_move(g.chain, mv); remove_from_hand_norm(g.hands[0], mv.dom)
                            g.belief.mark_played(mv.dom, 0); g.passes_in_row = 0; g.current = (g.current + 1) % 4
                            schedule_ai_if_needed()
                    elif dropR.collidepoint(mx,my) and ('R' in sides or 'OPEN' in sides):
                        mv = next((m for s,m in legal if s in ('R','OPEN')), None)
                        if mv:
                            g.chain = apply_move(g.chain, mv); remove_from_hand_norm(g.hands[0], mv.dom)
                            g.belief.mark_played(mv.dom, 0); g.passes_in_row = 0; g.current = (g.current + 1) % 4
                            schedule_ai_if_needed()
                dragging=False; selected=None

        # ================= Update =================
        if not in_menu:
            now = pygame.time.get_ticks()
            if (g.current != 0 and not g.round_over() and not show_next_round_btn and not match_over_prompt):
                if not ai_waiting:
                    schedule_ai_if_needed()
                if ai_waiting and now >= ai_next_time:
                    g.step_ai()  # una jugada
                    if g.current != 0 and not g.round_over():
                        ai_next_time = now + AI_DELAY_MS
                        ai_waiting = True
                    else:
                        ai_waiting = False

            if g.round_over() and not show_next_round_btn and not match_over_prompt:
                a,b = g.round_score()
                g.scores[0]+=a; g.scores[1]+=b
                last_round_points=(a,b)
                history.insert(0, f"Ronda: A+{a}  B+{b}  →  A={g.scores[0]}  B={g.scores[1]}")
                history[:] = history[:10]
                show_next_round_btn = True
                ai_waiting = False
                if g.scores[0] >= 100 or g.scores[1] >= 100:
                    match_over_prompt = True

        # ================= Render =================
        screen.fill(BG)

        if in_menu:
            text(screen, "Dominó 2v2", W//2, H//2-140, 44, WHITE, center=True)
            text(screen, "Elige modo de juego", W//2, H//2-90, 28, WHITE, center=True, bold=False)
            pygame.draw.rect(screen, BTN, btn_normal, border_radius=10)
            pygame.draw.rect(screen, BTN, btn_training, border_radius=10)
            text(screen, "Jugar NORMAL", btn_normal.centerx, btn_normal.centery, 22, WHITE, center=True)
            text(screen, "Jugar MODO ENTRENAMIENTO", btn_training.centerx, btn_training.centery, 22, WHITE, center=True)
            text(screen, "Tip: T alterna entrenamiento, N alterna puntos/números", W//2, H-60, 18, GREY, center=True, bold=False)
            pygame.display.flip(); clock.tick(60); continue

        pygame.draw.rect(screen, PANEL, (0,0,W,90))
        text(screen, "Equipo A", 30, 12, 22, ACCENT_A)
        text(screen, f"{g.scores[0]}", 30, 38, 36, ACCENT_A)
        text(screen, "Equipo B", W-170, 12, 22, ACCENT_B)
        text(screen, f"{g.scores[1]}", W-90, 38, 36, ACCENT_B)
        text(screen, 'Modo: ' + ('NÚMEROS' if RENDER_NUMBERS else 'PUNTOS'), 200, 12, 18, WHITE, bold=False)
        center_txt = f"Turno: J{g.current}  |  Manos: {[len(h) for h in g.hands]}  |  Pases: {g.passes_in_row}"
        text(screen, center_txt, W//2, 45, 22, WHITE, center=True, bold=False)

        pygame.draw.rect(screen, PANEL, (W-300, 90, 300, H-90))
        text(screen, "Historial", W-280, 100, 22, WHITE)
        y_hist = 130
        for line in history:
            text(screen, line, W-290, y_hist, 18, WHITE, bold=False)
            y_hist += 22

        pygame.draw.rect(screen, DARK, tbl_rect, border_radius=12)
        pos = layout_chain_positions(g.chain, tbl_rect)

# Ya NO necesitamos prev_right: la cadena está orientada por reglas.
        for (x, y, row_parity), (a, b) in zip(pos, g.chain):
    # En filas impares (der→izq) mostramos el dom volteado
            dom_view = (b, a) if row_parity == 1 else (a, b)
            rotate90 = (a == b)  # mulas verticales
            draw_tile(screen, dom_view, x, y, rotate90=rotate90)
        if g.chain:
            text(screen, f"Extremos: {g.ends()}", tbl_rect.x+10, tbl_rect.y-28, 22, WHITE, bold=False)

        # Oponentes
        top_y = tbl_rect.y - 60
        for i in range(len(g.hands[2])):
            draw_back_tile(screen, 40 + i*24, top_y, TILE_W-28, TILE_H-18)
        text(screen, f"J2 ({len(g.hands[2])})", 40 + len(g.hands[2])*24 + 10, top_y-2, 18, ACCENT_A, bold=False)

        right_x = tbl_rect.x + tbl_rect.width + 10
        for i in range(len(g.hands[1])):
            draw_back_tile(screen, right_x, 160 + i*22, TILE_W-28, TILE_H-18)
        text(screen, f"J1 ({len(g.hands[1])})", right_x, 140, 18, ACCENT_B, bold=False)

        left_x = 10
        for i in range(len(g.hands[3])):
            draw_back_tile(screen, left_x, 160 + i*22, TILE_W-28, TILE_H-18)
        text(screen, f"J3 ({len(g.hands[3])})", left_x, 140, 18, ACCENT_B, bold=False)

        # Mano del jugador
        base_y = H-110
        for i, d in enumerate(g.hands[0]):
            if dragging and d == selected:
                continue
            draw_tile(screen, d, 20 + i*(TILE_W+8), base_y)

        # Zonas de drop + entrenamiento
        if not (show_next_round_btn or match_over_prompt):
            moves = legal_moves(g.chain, g.hands[0])
            can_play_any = len(moves) > 0

            canL = canR = False
            pL = pR = None
            if training_mode and g.chain:
                L,R = g.ends()
                opp = 1
                pL = estimate_play_prob(L, opp, g.belief, g.hands_sizes())
                pR = estimate_play_prob(R, opp, g.belief, g.hands_sizes())

            if dragging and selected:
                legal = [(mv.side, mv) for mv in moves if normalize(mv.dom)==normalize(selected)]
                sides = {s for s,_ in legal}
                canL = ('L' in sides) or ('OPEN' in sides)
                canR = ('R' in sides) or ('OPEN' in sides)

            pygame.draw.rect(screen, (60,60,60), dropL, border_radius=8)
            pygame.draw.rect(screen, (60,60,60), dropR, border_radius=8)
            if canL: pygame.draw.rect(screen, HL, dropL, width=3, border_radius=8)
            if canR: pygame.draw.rect(screen, HL, dropR, width=3, border_radius=8)
            lblL = "Soltar a la IZQUIERDA"
            lblR = "Soltar a la DERECHA"
            if training_mode and pL is not None and pR is not None:
                lblL += f"  (Rival puede: {int(pL*100)}%)"
                lblR += f"  (Rival puede: {int(pR*100)}%)"
            text(screen, lblL, dropL.centerx, dropL.centery-10, 18, WHITE, center=True, bold=False)
            text(screen, lblR, dropR.centerx, dropR.centery-10, 18, WHITE, center=True, bold=False)

            if g.current == 0:
                color = BTN if not can_play_any else (80,80,80)
                pygame.draw.rect(screen, color, btn_pass, border_radius=8)
                text(screen, "PASAR", btn_pass.centerx, btn_pass.centery-6, 20, WHITE, center=True, bold=True)
                hint = "(sin jugadas)" if not can_play_any else "(tienes jugadas)"
                text(screen, hint, btn_pass.centerx, btn_pass.centery+12, 14, (160,160,160), center=True, bold=False)

        if dragging and selected:
            draw_tile(screen, selected, drag_pos[0], drag_pos[1])

        if show_next_round_btn:
            text(screen, f"Ronda terminada. A+{last_round_points[0]}  B+{last_round_points[1]}", 20, 120, 24, WHITE)
            pygame.draw.rect(screen, BTN, (20,80,180,30), border_radius=8); text(screen, "Siguiente ronda", 30, 86, 22)
            pygame.draw.rect(screen, BTN, (220,80,140,30), border_radius=8); text(screen, "Salir", 230, 86, 22)

        if match_over_prompt:
            text(screen, "¡Partida terminada! ¿Jugar otra?", 20, 150, 26, WHITE)
            pygame.draw.rect(screen, BTN, (20,120,220,30), border_radius=8); text(screen, "Sí (nueva partida)", 30, 126, 22)
            pygame.draw.rect(screen, BTN, (260,120,140,30), border_radius=8); text(screen, "No (salir)", 270, 126, 22)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()
