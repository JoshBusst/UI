
import pygame
from datetime import datetime, timedelta
from typing import List, Tuple, Optional

from pygame import surface
from UI.core.UIElements import *
from UI.core.graphics import *





class Dataseries:
    def __init__(self, data: list):
        self.data: List[Tuple[datetime, float]] = data
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

        tstart, tend = times[0], times[-1]
        trng: float = max((tend - tstart).total_seconds(), 1)

        vmax, vmin = max(values), min(values)
        vrng: float = vmax - vmin

        return vmin, vmax, vrng, tstart, tend, trng
    
class Graph(UIElement):
    def __init__(self, rect: tuple, data: list[tuple]):
        super().__init__(rect)

        self.theme: GraphTheme = copy(DEFAULT_GRAPH_THEME)
        self.dataset: Dataseries = Dataseries(data)

        pad: int = 50
        self._sub_rect: pygame.Rect = pygame.Rect(pad, pad, self.rect.w - pad, self.rect.h - 2*pad)
        self._sub_surface: pygame.Surface = pygame.Surface(self._sub_rect.size, pygame.SRCALPHA)
        
    def _draw_axes(self) -> None:
        pygame.draw.line(self._surface, (200,200,200), self._sub_rect.topleft, self._sub_rect.bottomleft)
        pygame.draw.line(self._surface, (200,200,200), self._sub_rect.bottomleft, self._sub_rect.bottomright)

        extrema: tuple = self.dataset.compute_extrema()

        x_notches: int = 9
        y_notches: int = 9

        x_step: int = (self._sub_rect.w - self._sub_rect.x) // (x_notches + 1)
        y_step: int = (self._sub_rect.h - self._sub_rect.y) // (y_notches + 1)

        draw_axis_label: bool = True
        for i in range(self._sub_rect.x + x_step, self._sub_rect.w + x_step, x_step):
            draw_dashed_line(self._surface, (120,120,120,40), (i, self._sub_rect.h  + self._sub_rect.y), (i, 0), width=2)
            pygame.draw.line(self._surface, (200,200,200), (i, self._sub_rect.h  + self._sub_rect.y - 10), (i, self._sub_rect.h  + self._sub_rect.y + 10))

            if draw_axis_label:
                point: tuple = self._graph_to_point((i, self._sub_rect.h + self._sub_rect.y), extrema)
                label: pygame.Surface = self.theme.label_font.render(point[0].strftime("%H:%M:%S"), True, self.theme.text)
                self._surface.blit(label, label.get_rect(center=(i, self._sub_rect.h + self._sub_rect.y + 25)))
            
            draw_axis_label = not draw_axis_label
        
        for j in range(self._sub_rect.y, self._sub_rect.h + self._sub_rect.y, y_step):
            draw_dashed_line(self._surface, (120,120,120,40), (self._sub_rect.x, j), (self.rect.w, j), width=2)
            pygame.draw.line(self._surface, (200,200,200), (self._sub_rect.x - 10, j), (self._sub_rect.x + 10, j))
            
            point: tuple = self._graph_to_point((self._sub_rect.x, j), extrema)
            label: pygame.Surface = self.theme.label_font.render(str(int(point[1])), True, self.theme.text)
            self._surface.blit(label, label.get_rect(center=(self._sub_rect.x-25, j)))

    def _point_to_graph(self, point: tuple, extrema: tuple) -> float:
        vmin, vmax, vrng, tstart, tend, trng = extrema

        i: float = (self._sub_rect.w * (point[0] - tstart).total_seconds()) // trng
        j: float = self._sub_rect.h - (self._sub_rect.h * (point[1] - vmin)) // vrng

        return i, j

    def _graph_to_point(self, point: tuple, extrema: tuple) -> tuple:
        vmin, vmax, vrng, tstart, tend, trng = extrema

        i, j = point

        # Invert x to timestamp
        t_seconds = (i * trng) / self._sub_rect.w
        t = tstart + timedelta(seconds=t_seconds)

        # Invert y to value
        v = vmin + ((self._sub_rect.h - j) * vrng) / self._sub_rect.h

        return t, v

    def _convert_points(self, dataseries: Dataseries) -> list[tuple]:
        extrema: tuple = dataseries.compute_extrema()

        return [self._point_to_graph(point, extrema) for point in self.dataset.data]
    
    def _draw_point_dots(self, surface: pygame.Surface, points: list[tuple], size: int=2) -> None:
        for point in points:
            pygame.draw.circle(surface, self.theme.muted, point, size)

    def render(self) -> None:
        self._surface.fill(self.theme.bg)
        self._surface.fill(self.theme.panel, self._sub_rect)

        self._sub_surface.fill((0,0,0,0))

        # draw the main graph
        graph_points: list[tuple] = self._convert_points(self.dataset)

        pygame.draw.aalines(self._sub_surface, self.theme.muted, False, graph_points)
        self._draw_point_dots(self._sub_surface, graph_points)

        self._draw_axes()
        self._surface.blit(self._sub_surface, self._sub_rect)

    def handle_event(self, event: pygame.event.Event) -> None:
        pass

class Legend(Canvas):
    def __init__(self, rect: tuple, entries: List[str]):
        super().__init__(rect)
        self.entries = entries



class Chart(Canvas):
    def __init__(
        self,
        rect: tuple,
        data: Dataseries,
        title: str = "",
        x_label: str = "",
        y_label: str = "",
        legend: List[str] = None,
    ):
        super().__init__(rect)

        self._surface = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        self._rerender = True
        self.theme: Theme = DEFAULT_GRAPH_THEME

        # Labels
        self.title: Label = Label((0, 0, self.rect.width, 30), title)
        self.x_label: Label = Label((0, 0, self.rect.width, 30), x_label)
        self.x_label.rect.center = (self.rect.w // 2, self.rect.h - 20)
        self.y_label: Label = Label((0, 0, self.rect.h, 30), y_label)
        self.y_label.angle = 90
        self.y_label.rect.center = (20, self.rect.h // 2)
        self.legend: Legend = Legend((0,0,100,100), legend)

        pad: int = 40
        self._add_elem(
            self.title,
            self.x_label,
            self.y_label,
            # self.legend,
            Graph((pad,pad,self.rect.w - 2*pad,self.rect.h - 2*pad), data)
        )

        self.padding = 60
        self.point_radius = 4
        self.tick_count = 5

    def add_point(self, timestamp: datetime, value: float) -> None:
        self.data.append((timestamp, value))
        self.data.sort(key=lambda d: d[0])
        self._rerender = True

    def set_data(self, data: List[Tuple[datetime, float]]) -> None:
        self.data = sorted(data, key=lambda d: d[0])
        self._rerender = True

    def handle_event(self, event: pygame.event.Event) -> None:
        pass

