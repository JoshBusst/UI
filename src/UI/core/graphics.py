
import pygame
from math import hypot

pygame.init()


# ==================== DEFAULT_THEME ====================
DEFAULT_THEME = {
    "bg": (33, 24, 18),
    "panel": (64, 44, 28),
    "transparent": (0,0,0,0),

    "elem": (198, 170, 128),
    "elem_hover": (210, 182, 140),
    "elem_pressed": (180, 152, 112),
    "elem_clicked": (160, 132, 102),

    "text": (248, 246, 240),
    "muted": (215, 210, 200),
    "elem_text": (40, 30, 22),
}


# ---------- Default Fonts ----------
FONT_SMALL = pygame.font.SysFont("segoeui", 12)
FONT_MED = pygame.font.SysFont("segoeui", 24)
FONT_LARGE = pygame.font.SysFont("segoeui", 36)

HEADER_HEIGHT: int = 120
FOOTER_HEIGHT: int = 90



def draw_dashed_line(surface: pygame.surface, colour: tuple, start: tuple, end: tuple, dash_len: int=6, gap: int=6, width: int=1):
    x1, y1 = start
    x2, y2 = end

    dx = x2 - x1
    dy = y2 - y1

    length = hypot(dx, dy)
    if length == 0:
        return

    ux = dx / length
    uy = dy / length

    step = dash_len + gap
    dist = 0

    while dist < length:
        start_dash = dist
        end_dash = min(dist + dash_len, length)

        sx = x1 + ux * start_dash
        sy = y1 + uy * start_dash
        ex = x1 + ux * end_dash
        ey = y1 + uy * end_dash

        pygame.draw.line(surface, colour, (sx, sy), (ex, ey), width)

        dist += step