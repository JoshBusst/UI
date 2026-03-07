
import pygame
from datetime import datetime, timedelta
from typing import List, Tuple, Optional

from pygame import surface
from UI.core.UIElements import *
from UI.core.graphics import draw_dashed_line


GRAPH_DEFAULT_THEME = {
    "bg": (25, 25, 28),
    "elem": (200, 200, 220),
    "tick": (150, 150, 170),
    "grid": (150, 150, 170, 70),
}


class DataSeries:
    def __init__(self):
        self.data: List[Tuple[datetime, float]] = []
        self.auto_sort: bool = True

    def size(self) -> int:
        return len(self.data)
    
    def add_point(self, timestamp: datetime, value: float) -> None:
        self.data.append((timestamp, value))
        
        if self.auto_sort:
            self.data.sort(key=lambda d: d[0])

    def compute_extrema(self) -> tuple:
        if len(self.data) < 2:
            return None

        values: list[float] = [v for _, v in self.data]
        times: list[datetime] = [t for t, _ in self.data]

        tstart, tend = times[0], times[1]
        trng: float = max((tend - tstart).total_seconds(), 1)

        vmax, vmin = max(values), min(values)
        vrng: float = vmax - vmin

        return vmin, vmax, vrng, tstart, tend, trng
    
class Graph2(UIElement):
    def __init__(self, rect: pygame.Rect):
        super().__init__(rect)
        self._surface = pygame.Surface(self.rect.size, pygame.SRCALPHA)

        self.dataset: DataSeries = DataSeries()
        self.padding: int = 40

        # padding keeps space left and lower for labels and ticks
        self._graph_rect = pygame.Rect(
            self.padding,
            0,
            self.rect.width - self.padding,
            self.rect.height - self.padding,
        )

    def graph_point(self, point: tuple) -> tuple:
        x, y = point
        return (x - self.rect.x, y - self.rect.y)
    
    def _draw_axes(self, vmin: float, vmax: float, vrng: float, tstart: datetime, tend: datetime, trng: float) -> None:
        topleft: tuple = (self._graph_rect.x, self._graph_rect.y)
        bottomleft: tuple = (self._graph_rect.x, self._graph_rect.y + self._graph_rect.h - 1)
        bottomright: tuple = (self._graph_rect.x + self._graph_rect.w - 1, self._graph_rect.y + self._graph_rect.h - 1)

        pygame.draw.line(self._surface, GRAPH_DEFAULT_THEME["tick"], topleft, bottomleft, 1)
        pygame.draw.line(self._surface, GRAPH_DEFAULT_THEME["tick"], bottomleft, bottomright, 1)

        if self.dataset.size() < 2:
            return

        # vmin, vmax, vrng, tstart, tend, trng = self.dataset.compute_extrema()
        tick_count: int = 5

        # for i in range(tick_count):
        #     # X grid
        #     x: float = self.rect.left + i * (self.rect.width / tick_count)
        #     self._draw_dashed_line((x, self.rect.top), (x, self.rect.bottom))

        #     t_val: datetime = tstart + timedelta(seconds=trng * (i / tick_count))
        #     label: str = t_val.strftime("%H:%M:%S")
        #     text: pygame.Surface = FONT_SMALL.render(label, True, GRAPH_DEFAULT_THEME["tick"])
        #     self._surface.blit(text, (x - text.get_width() // 2, self.rect.bottom + 8))

        #     # Y grid
        #     y: float = self.rect.top + i * (self.rect.height / tick_count)
        #     self._draw_dashed_line((self.rect.left, y), (self.rect.right, y))

        #     value: float = vmax - (i / tick_count) * (vmax - vmin)
        #     label: str = f"{value:.2f}"
        #     text: pygame.Surface = FONT_SMALL.render(label, True, GRAPH_DEFAULT_THEME["tick"])
        #     self._surface.blit(text, (self.rect.left - text.get_width() - 8, y - text.get_height() // 2))

    def _draw_dashed_line(self, start: tuple, end: tuple, dash=6):
        x1, y1 = start
        x2, y2 = end

        dx = x2 - x1
        dy = y2 - y1
        length = max(abs(dx), abs(dy))
        if length == 0:
            return

        for i in range(0, length, dash * 2):
            f1 = i / length
            f2 = min((i + dash) / length, 1)
            sx = x1 + dx * f1
            sy = y1 + dy * f1
            ex = x1 + dx * f2
            ey = y1 + dy * f2
            pygame.draw.line(self._surface, GRAPH_DEFAULT_THEME["grid"], (sx, sy), (ex, ey), 1)

    def handle_event(self, event: pygame.event.Event) -> None:
        print(event.pos)
    
    def draw(self, surface: pygame.Surface) -> None:
        self._surface.fill(GRAPH_DEFAULT_THEME["bg"])

        # if len(self.dataset.data) >= 2:
        #     points = self._compute_points(self.dataset.data)
        #     pygame.draw.aalines(self._surface, self.line_color, False, points)

        #     for pt in points:
        #         pygame.draw.circle(self._surface, self.point_color, pt, self.point_radius)

        extrema: tuple = self.dataset.compute_extrema()
        if extrema:
                self._draw_axes(*extrema)

        surface.blit(self._surface, self.rect.topleft)

class Graph(UIElement):
    def __init__(self, rect: pygame.Rect, data: Optional[DataSeries] = None):
        super().__init__(rect)

        self._surface = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        self._rerender = True

        # DataSeries backing store; create a fresh one if caller didn't supply
        self.data: DataSeries = data if data is not None else DataSeries()

        # Style
        self.bg_color = (25, 25, 28)
        self.line_color = DEFAULT_THEME["elem"]
        self.point_color = DEFAULT_THEME["elem_hover"]
        self.tick_color = DEFAULT_THEME["muted"]
        self.grid_color = (*DEFAULT_THEME["muted"], 70)
        self.legend_bg = (35, 35, 40)

        self.padding = 60
        self.point_radius = 4
        self.tick_count = 5

        # Fonts
        self.title_font = pygame.font.SysFont("consolas", 18, bold=True)
        self.label_font = pygame.font.SysFont("consolas", 14)
        self.tick_font = pygame.font.SysFont("consolas", 12)

    # ------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------

    def add_point(self, timestamp: datetime, value: float) -> None:
        """Append a new sample via DataSeries and flag redraw."""
        self.data.add_point(timestamp, value)
        self._rerender = True

    def set_data(self, data: List[Tuple[datetime, float]]) -> None:
        """Replace the underlying series with the provided list."""
        new_series = DataSeries()
        for t, v in sorted(data, key=lambda d: d[0]):
            new_series.add_point(t, v)
        self.data = new_series
        self._rerender = True

    # ------------------------------------------------------------
    # Layout Helpers
    # ------------------------------------------------------------

    def _graph_rect(self) -> pygame.Rect:
        return pygame.Rect(
            self.padding,
            self.padding,
            self.rect.width - 2 * self.padding,
            self.rect.height - 2 * self.padding,
        )

    # ------------------------------------------------------------
    # Projection
    # ------------------------------------------------------------

    @staticmethod
    def _compute_points(data: list, graph_rect: pygame.Rect) -> tuple:
        if len(data) < 2:
            return [], 0, 1, None, None

        pts = sorted(data, key=lambda t_v: t_v[0])
        times, vals = zip(*pts)

        t0 = times[0]
        t1 = times[-1]
        total_time = max((t1 - t0).total_seconds(), 1)

        vmin = min(vals)
        vmax = max(vals)
        if vmin == vmax:
            vmax = vmin + 1

        points = []

        for t, v in pts:
            x_frac = (t - t0).total_seconds() / total_time
            x = graph_rect.left + int(x_frac * graph_rect.width)

            y_frac = (v - vmin) / (vmax - vmin)
            y = graph_rect.bottom - int(y_frac * graph_rect.height)

            points.append((x, y))

        return points, vmin, vmax, t0, t1

    # ------------------------------------------------------------
    # Coordinate conversion
    # ------------------------------------------------------------

    def graph_to_data(self, coord: tuple) -> Optional[Tuple[datetime, float]]:
        if len(self.data.data) < 2:
            return None

        # replicate the projection calculations from _compute_points so that we
        # can invert them.  note that _compute_points always sorts the data.
        pts = sorted(self.data.data, key=lambda t_v: t_v[0])
        times, vals = zip(*pts)

        t0 = times[0]
        t1 = times[-1]
        total_secs = max((t1 - t0).total_seconds(), 1)

        vmin = min(vals)
        vmax = max(vals)
        if vmin == vmax:
            vmax = vmin + 1

        gx, gy = coord

        # clamp to graph area
        gx = max(0, min(gx, self.rect.width))
        gy = max(0, min(gy, self.rect.height))

        # invert x -> time
        frac_x = gx / self.rect.width
        timestamp = t0 + timedelta(seconds=frac_x * total_secs)

        # invert y -> value (note Y is top=0, bottom=height)
        frac_y = 1 - (gy / self.rect.height)
        value = vmin + frac_y * (vmax - vmin)

        return timestamp, value

    # ------------------------------------------------------------
    # Grid / Axes / Labels
    # ------------------------------------------------------------

    def _draw_dashed_line(self, start: tuple, end: tuple, dash=6):
        x1, y1 = start
        x2, y2 = end

        dx = x2 - x1
        dy = y2 - y1
        length = max(abs(dx), abs(dy))
        if length == 0:
            return

        for i in range(0, length, dash * 2):
            f1 = i / length
            f2 = min((i + dash) / length, 1)
            sx = x1 + dx * f1
            sy = y1 + dy * f1
            ex = x1 + dx * f2
            ey = y1 + dy * f2
            pygame.draw.line(self._surface, self.grid_color, (sx, sy), (ex, ey), 1)

    def _draw_axes(self, graph_rect, vmin, vmax, t0, t1):
        pygame.draw.line(self._surface, self.tick_color, graph_rect.bottomleft, graph_rect.bottomright, 1)
        pygame.draw.line(self._surface, self.tick_color, graph_rect.topleft, graph_rect.bottomleft, 1)

        if not self.data:
            return

        total_time = max((t1 - t0).total_seconds(), 1)

        for i in range(self.tick_count + 1):
            # X grid
            x = graph_rect.left + i * (graph_rect.width / self.tick_count)
            self._draw_dashed_line((x, graph_rect.top), (x, graph_rect.bottom))

            t_val = t0 + timedelta(seconds=total_time * (i / self.tick_count))
            label = t_val.strftime("%H:%M:%S")
            text = self.tick_font.render(label, True, self.tick_color)
            self._surface.blit(text, (x - text.get_width() // 2, graph_rect.bottom + 8))

            # Y grid
            y = graph_rect.top + i * (graph_rect.height / self.tick_count)
            self._draw_dashed_line((graph_rect.left, y), (graph_rect.right, y))

            value = vmax - (i / self.tick_count) * (vmax - vmin)
            label = f"{value:.2f}"
            text = self.tick_font.render(label, True, self.tick_color)
            self._surface.blit(text, (graph_rect.left - text.get_width() - 8, y - text.get_height() // 2))

    # ------------------------------------------------------------
    # Render
    # ------------------------------------------------------------

    def render(self) -> None:
        self._surface.fill(self.bg_color)

        # pull the raw list from the DataSeries for projection
        points, vmin, vmax, t0, t1 = self._compute_points(self.data.data, self.rect)

        self._draw_axes(self.rect, vmin, vmax, t0, t1)

        if len(points) >= 2:
            pygame.draw.aalines(self._surface, self.line_color, False, points)

        for pt in points:
            pygame.draw.circle(self._surface, self.point_color, pt, self.point_radius)

    # ------------------------------------------------------------
    # Required Interface
    # ------------------------------------------------------------

    def draw(self, surface: pygame.Surface) -> None:
        if self._rerender:
            self._rerender = False
            self.render()
            
        surface.blit(self._surface, self.rect.topleft)

    def handle_event(self, event: pygame.event.Event) -> None:
        pass

class Legend(Canvas):
    def __init__(self, rect: pygame.Rect, entries: List[str]):
        super().__init__(rect)
        self.entries = entries


class Chart(Canvas):
    def __init__(
        self,
        rect: pygame.Rect,
        data: DataSeries,
        title: str = "",
        x_label: str = "",
        y_label: str = "",
        legend: Optional[List[str]] = None,
    ):
        super().__init__(rect)

        self._surface = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        self._rerender = True

        # Labels
        self.title: Label = Label(pygame.Rect(0, 0, self.rect.width, 30), title)
        self.x_label: Label = Label(pygame.Rect(0, 0, self.rect.width, 20), x_label)
        self.y_label: Label = Label(pygame.Rect(0, 0, self.rect.width, 20), y_label)
        self.legend: Legend = None

        self._add_elem(
            self.title,
            self.x_label,
            self.y_label
        )

        # Style
        self.bg_color = (20,10,10)
        self.line_color = DEFAULT_THEME["elem"]
        self.point_color = DEFAULT_THEME["elem_hover"]
        self.tick_color = DEFAULT_THEME["muted"]
        self.grid_color = (*DEFAULT_THEME["muted"], 70)
        self.legend_bg = (35, 35, 40)

        self.padding = 60
        self.point_radius = 4
        self.tick_count = 5

        # Fonts
        self.title_font = pygame.font.SysFont("consolas", 18, bold=True)
        self.label_font = pygame.font.SysFont("consolas", 14)
        self.tick_font = pygame.font.SysFont("consolas", 12)

    # ------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------

    def add_point(self, timestamp: datetime, value: float) -> None:
        self.data.append((timestamp, value))
        self.data.sort(key=lambda d: d[0])
        self._rerender = True

    def set_data(self, data: List[Tuple[datetime, float]]) -> None:
        self.data = sorted(data, key=lambda d: d[0])
        self._rerender = True

    def draw(self, surface: pygame.Surface) -> None:
        self._surface.fill(self.bg_color)
        surface.blit(self._surface, self.rect.topleft)
        super().draw(surface)

    def handle_event(self, event: pygame.event.Event) -> None:
        pass

