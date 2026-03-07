
import pygame
from math import hypot

pygame.init()



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