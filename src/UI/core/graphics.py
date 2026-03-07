
import pygame
from math import hypot

pygame.init()



# ==================== DEFAULT_THEME ====================
class Theme:
    # static themes
    bg: tuple = (33, 24, 18)
    panel: tuple = (64, 44, 28)
    border: tuple = (0,0,0)

    # static and reactive element styles
    elem: tuple = (198, 170, 128)
    elem_hover: tuple = (210, 182, 140)
    elem_pressed: tuple = (180, 152, 112)
    elem_clicked: tuple = (160, 132, 102)

    # text
    text: tuple = (248, 246, 240)
    muted: tuple = (215, 210, 200)
    font: pygame.font.Font = pygame.font.SysFont("segoeui", 24)

    def print(self) -> None:
        print(f"Elements of: {self.__class__.__name__}")

        for attr in dir(self):
            if callable(attr) or attr.startswith("_"):
                continue

            print(f"  > {attr}")

class CheckboxTheme(Theme):
    border: tuple = (0,0,0)

class ChartTheme(Theme):
    bg: tuple = (25, 25, 28)
    elem: tuple = (200, 200, 220)
    tick: tuple = (150, 150, 170)
    legend: tuple = (35, 35, 40)
    grid: tuple = (*Theme.muted[:3], 70)

    title_font: pygame.font.Font = pygame.font.SysFont("consolas", 18, bold=True)
    label_font: pygame.font.Font = pygame.font.SysFont("consolas", 14)
    tick_font: pygame.font.Font = pygame.font.SysFont("consolas", 12)

class ButtonTheme(Theme):
    text: tuple = (10,10,10)

class LabelTheme(Theme):
    bg: tuple = (0,0,0,0)
    font: tuple = pygame.font.SysFont("segoeui", 32, bold=True)


DEFAULT_THEME: Theme = Theme()
DEFAULT_CHART_THEME: Theme = ChartTheme()
DEFAULT_CHECKBOX_THEME: Theme = CheckboxTheme()
BUTTON_DEFAULT_THEME: Theme = ButtonTheme()
DEFAULT_LABEL_THEME: Theme = LabelTheme()

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



if __name__ == "__main__":
    DEFAULT_THEME.print()