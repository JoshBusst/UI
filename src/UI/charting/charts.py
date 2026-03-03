
import pygame
from datetime import datetime, timedelta
from typing import List, Tuple, Optional
from UI.core.UIElements import UIElement, DEFAULT_THEME


class Chart(UIElement):
    def __init__(
        self,
        rect: pygame.Rect,
        data: Optional[List[Tuple[datetime, float]]] = None,
        title: str = "",
        x_label: str = "",
        y_label: str = "",
        legend: Optional[List[str]] = None,
    ):
        super().__init__(rect)

        self._surface = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        self._rerender = True

        # Data
        self.data: List[Tuple[datetime, float]] = sorted(data or [], key=lambda d: d[0])

        # Labels
        self.title = title
        self.x_label = x_label
        self.y_label = y_label
        self.legend = legend or []

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
        self.data.append((timestamp, value))
        self.data.sort(key=lambda d: d[0])
        self._rerender = True

    def set_data(self, data: List[Tuple[datetime, float]]) -> None:
        self.data = sorted(data, key=lambda d: d[0])
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

    def _graph_point(self, point: tuple) -> tuple:
        graph_rect = self._graph_rect()
        x, y = point
        return (x - graph_rect.x, y - graph_rect.y)

    # ------------------------------------------------------------
    # Coordinate conversion
    # ------------------------------------------------------------

    def graph_to_data(self, coord: tuple) -> Optional[Tuple[datetime, float]]:
        if len(self.data) < 2:
            return None

        # replicate the projection calculations from _compute_points so that we
        # can invert them.  note that _compute_points always sorts the data.
        pts = sorted(self.data, key=lambda t_v: t_v[0])
        times, vals = zip(*pts)

        t0 = times[0]
        t1 = times[-1]
        total_secs = max((t1 - t0).total_seconds(), 1)

        vmin = min(vals)
        vmax = max(vals)
        if vmin == vmax:
            vmax = vmin + 1

        graph_rect = self._graph_rect()
        gx, gy = coord

        # clamp to graph area
        gx = max(0, min(gx, graph_rect.width))
        gy = max(0, min(gy, graph_rect.height))

        # invert x -> time
        frac_x = gx / graph_rect.width
        timestamp = t0 + timedelta(seconds=frac_x * total_secs)

        # invert y -> value (note Y is top=0, bottom=height)
        frac_y = 1 - (gy / graph_rect.height)
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
    # Titles & Legend
    # ------------------------------------------------------------

    def _draw_titles(self):
        # Chart title
        if self.title:
            text = self.title_font.render(self.title, True, self.line_color)
            self._surface.blit(
                text,
                ((self.rect.width - text.get_width()) // 2, 10),
            )

        # X label
        if self.x_label:
            text = self.label_font.render(self.x_label, True, self.tick_color)
            self._surface.blit(
                text,
                (
                    self.rect.width // 2 - text.get_width() // 2,
                    self.rect.height - text.get_height() - 10,
                ),
            )

        # Y label (rotated)
        if self.y_label:
            text = self.label_font.render(self.y_label, True, self.tick_color)
            text = pygame.transform.rotate(text, 90)
            self._surface.blit(
                text,
                (10, self.rect.height // 2 - text.get_height() // 2),
            )

    def _draw_legend(self):
        if not self.legend:
            return

        padding = 8
        line_height = 18
        width = 120
        height = padding * 2 + len(self.legend) * line_height

        legend_rect = pygame.Rect(
            self.rect.width - width - 15,
            15,
            width,
            height,
        )

        pygame.draw.rect(self._surface, self.legend_bg, legend_rect, border_radius=6)
        pygame.draw.rect(self._surface, self.tick_color, legend_rect, 1, border_radius=6)

        for i, entry in enumerate(self.legend):
            y = legend_rect.top + padding + i * line_height

            # color box
            pygame.draw.rect(
                self._surface,
                self.line_color,
                (legend_rect.left + 6, y + 4, 10, 10),
            )

            text = self.label_font.render(entry, True, self.tick_color)
            self._surface.blit(text, (legend_rect.left + 22, y))

    # ------------------------------------------------------------
    # Render
    # ------------------------------------------------------------

    def render(self) -> None:
        self._surface.fill(self.bg_color)

        graph_rect = self._graph_rect()
        points, vmin, vmax, t0, t1 = self._compute_points(self.data, graph_rect)

        self._draw_axes(graph_rect, vmin, vmax, t0, t1)
        self._draw_titles()
        self._draw_legend()

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


