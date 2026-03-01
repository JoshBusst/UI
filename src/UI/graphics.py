from numpy import array, rec, linspace, sin
import matplotlib.pyplot as plt
from matplotlib import dates as mdates
import pygame
from datetime import datetime
from abc import ABC, abstractmethod
from UI.worker import log, Mailbox, _content_interface



pygame.init()

SCREEN_SIZE: tuple[int] = (900,900)
SCREEN_WIDTH, SCREEN_HEIGHT = SCREEN_SIZE


# ==================== DEFAULT_THEME ====================
DEFAULT_THEME = {
    "bg": (33, 24, 18),
    "panel": (64, 44, 28),

    "elem": (198, 170, 128),
    "elem_hover": (210, 182, 140),
    "elem_pressed": (180, 152, 112),
    "elem_clicked": (160, 132, 102),

    "text": (248, 246, 240),
    "muted": (215, 210, 200),
    "elem_text": (40, 30, 22),
}


# ==================== FONTS ====================
FONT_SMALL = pygame.font.SysFont("segoeui", 12)
FONT_MED = pygame.font.SysFont("segoeui", 24)
FONT_LARGE = pygame.font.SysFont("segoeui", 36, bold=True)

HEADER_HEIGHT: int = 120
FOOTER_HEIGHT: int = 90

CONTENT_RECT = pygame.Rect(
    0,
    HEADER_HEIGHT,
    SCREEN_WIDTH,
    SCREEN_HEIGHT - HEADER_HEIGHT - FOOTER_HEIGHT
)

MOUSE_BUTTON_LEFT: int = 1
MOUSE_BUTTON_MID: int = 2
MOUSE_BUTTON_RIGHT: int = 3
MOUSE_EVENTS: tuple = (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION)



def localEvent(event: pygame.event.Event, rect: pygame.Rect) -> pygame.event.Event:
    """Relativise an event position to a local rect."""
    if event.type == pygame.MOUSEMOTION:
        return pygame.event.Event(event.type, {
            'pos': (event.pos[0] - rect.x, event.pos[1] - rect.y),
            'rel': event.rel,
            'buttons': event.buttons,
        })
    else:
        return pygame.event.Event(event.type, {
            'pos': (event.pos[0] - rect.x, event.pos[1] - rect.y),
            'button': event.button,
        })



# the base UIElement class
class UIElement(ABC):
    def __init__(self, rect: pygame.Rect):
        self._render: bool = True
        self._surface: pygame.Surface = None

        self.rect: pygame.Rect = rect
        self.interactable: bool = True
        self.visible: bool = True

    @abstractmethod
    def draw(self, surface: pygame.Surface) -> None:
        pass

    @abstractmethod
    def handle_event(self, event: pygame.event.Event) -> None:
        pass



class Button(UIElement):
    """A toggle button. State is toggled on each click, and button is visually depressed while active."""

    def __init__(self, rect: pygame.Rect, text: str="", callback: callable=None):
        super().__init__(rect)

        self._anim_rect: pygame.Rect = rect.copy() # used for animation
        self._callback: callable = callback
        self._pressed: bool = False
        self._mouse_hover: bool = False
        self._surface: pygame.Surface = pygame.Surface(self.rect.size, pygame.SRCALPHA)

        self.text: str = text
        self.state: bool = False
        self.font: pygame.font.Font = FONT_MED
    
    def rerender(self) -> None:
        self._anim_rect = self.rect.copy()

        if self._pressed:
            colour = DEFAULT_THEME["elem_pressed"]
            self._anim_rect = self._anim_rect.move(0, 4)
        elif self.state:
            colour = DEFAULT_THEME["elem_clicked"]
            self._anim_rect = self._anim_rect.move(0, 2)
        elif self._mouse_hover:
            colour = DEFAULT_THEME["elem_hover"]
        else:
            colour = DEFAULT_THEME["elem"]

        # render button background and label text
        pygame.draw.rect(self._surface, colour, pygame.Rect(0,0,*self._anim_rect.size), border_radius=14)
        textSurface: pygame.surface = FONT_MED.render(self.text, True, DEFAULT_THEME["elem_text"])

        self._surface.blit(textSurface, textSurface.get_rect(center=self._surface.get_rect().center))

    def draw(self, surface: pygame.Surface) -> None:
        if self._render:
            self._render = False
            self.rerender()

        if self.visible:
            surface.blit(self._surface, self._surface.get_rect(center=self._anim_rect.center))

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type not in [pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION] or not self.interactable:
            return False
        
        if self.rect.collidepoint(event.pos):
            self._mouse_hover = True

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == MOUSE_BUTTON_LEFT:
                self._pressed = True

            elif event.type == pygame.MOUSEBUTTONUP and event.button == MOUSE_BUTTON_LEFT and self._pressed:
                self._pressed = False
                self.state = not self.state

                if self.state:
                    self._callback()
                    return True
        else:
            self._mouse_hover = False
            self._pressed = False

        self._render = True
        return False

class Button_Tap(Button):
    """A quick-tap button variant. State is not toggled, and button is only visually depressed while held."""

    def __init__(self, rect, text = "", callback = None):
        super().__init__(rect, text, callback)

    def handle_event(self, event: pygame.event.Event) -> None:
        super().handle_event(event)

        if self.state:
            self.state = False

class Checkbox(Button):
    def __init__(self, rect: pygame.Rect, text: str="", callback: callable=None, check_type: str="tick", font: pygame.font.Font=FONT_MED):
        super().__init__(rect, text, callback)
        self._type_renders: dict[str, callable] = {
            "tick": self.render_tick,
            "cross": self.render_cross,
            "asterisk": self.render_asterisk,
            "dash": self.render_dash,
            "solid": self.render_solid,
        }

        self.check_type: str = check_type
        self.box_padding: int = 20
        self.box_colour: tuple = (0,0,0)
        self.check_colour: tuple = (0,0,0)
        self.text_colour: tuple = (0,0,0)
        self.font: pygame.font.Font = font

    def rerender(self) -> None:
        """Render an animated checkbox surface."""

        size = self.rect.h - self.box_padding
        surface = pygame.Surface((size, size), pygame.SRCALPHA)


        # --- Draw check mark ---
        if self.state:
            if self.check_type in self._type_renders:
                self._type_renders[self.check_type](surface, size, self.check_colour)
            else:
                log(f"Unknown checkbox type '{self.check_type}'! Defaulting to tick.")
                self._type_renders["tick"](surface, size, self.check_colour)
        
        # --- Scaled values ---
        border_width = max(2, size // 12)

        # --- render outer box ---
        pygame.draw.rect(
            surface,
            self.box_colour,
            pygame.Rect(0, 0, size, size),
            border_width,
            border_radius=size // 8,
        )

        # render checkbox
        self._surface.fill(DEFAULT_THEME["elem"])
        pad: int = (self.rect.height - size) // 2
        self._surface.blit(surface, (pad,pad))
        
        # render display text
        textSurface: pygame.surface = self.font.render(self.text, True, self.text_colour)
        self._surface.blit(textSurface, (pad*2 + size, (self.rect.height - textSurface.get_height()) // 2))

    @staticmethod
    def render_tick(surface: pygame.Surface, size: int, colour: tuple) -> None:
        tick_width = max(2, size // 10)
    
        # Tick key points (percentage based)
        start = (size * 0.28, size * 0.55)
        mid   = (size * 0.45, size * 0.72)
        end   = (size * 0.75, size * 0.30)

        pygame.draw.line(surface, colour, start, mid, tick_width)

        # Animate second segment
        x = mid[0] + (end[0] - mid[0])
        y = mid[1] + (end[1] - mid[1])
        pygame.draw.line(surface, colour, mid, (x, y), tick_width)
    
    @staticmethod
    def render_cross(surface: pygame.Surface, size: int, colour: tuple) -> None:
        width = max(2, size // 10)

        padding = size * 0.25

        pygame.draw.line(
            surface,
            colour,
            (padding, padding),
            (size - padding, size - padding),
            width,
        )

        pygame.draw.line(
            surface,
            colour,
            (size - padding, padding),
            (padding, size - padding),
            width,
        )

    @staticmethod
    def render_asterisk(surface: pygame.Surface, size: int, colour: tuple) -> None:
        width = max(2, size // 12)
        center = size * 0.5
        pad_diag = size * 0.25
        pad_straight: int = size * 0.20

        # Horizontal
        pygame.draw.line(surface, colour,
                        (pad_straight, center),
                        (size - pad_straight, center),
                        width)

        # Vertical
        pygame.draw.line(surface, colour,
                        (center, pad_straight),
                        (center, size - pad_straight),
                        width)

        # Diagonal 1
        pygame.draw.line(surface, colour,
                        (pad_diag, pad_diag),
                        (size - pad_diag, size - pad_diag),
                        width)

        # Diagonal 2
        pygame.draw.line(surface, colour,
                        (size - pad_diag, pad_diag),
                        (pad_diag, size - pad_diag),
                        width)

    @staticmethod
    def render_dash(surface: pygame.Surface, size: int, colour: tuple) -> None:
        width = max(2, size // 10)

        y = size * 0.5
        start = (size * 0.25, y)
        end   = (size * 0.75, y)

        pygame.draw.line(surface, colour, start, end, width)

    @staticmethod
    def render_solid(surface: pygame.Surface, size: int, colour: tuple) -> None:
        padding = size * 0

        rect = pygame.Rect(
            padding,
            padding,
            size - padding * 2,
            size - padding * 2,
        )

        pygame.draw.rect(surface, colour, rect, border_radius=size // 8)

    @staticmethod
    def checkbox_types() -> list[str]:
        return list(Checkbox._type_renders.keys())


# a simple text label
class Label(UIElement):
    def __init__(self, rect: pygame.Rect, text: str="", font: pygame.font.Font=FONT_MED, color: tuple=(255,255,255)):
        super().__init__(rect)

        self.text: str = text
        self.font: pygame.font.Font = font
        self.color: tuple = color

    def draw(self, surface: pygame.Surface) -> None:
        label = self.font.render(self.text, True, self.color)
        surface.blit(label, label.get_rect(topleft=(self.rect.x, self.rect.y)))

    def handle_event(self, event: pygame.event.Event) -> None:
        pass

# a dynamic content pane. Points to a mailbox for content collection
class ContentPane(UIElement):
    def __init__(self, rect: pygame.Rect, channel: str):
        super().__init__(rect)

        self._channel: str = channel
        self._surface: pygame.Surface = pygame.Surface(self.rect.size)
        self._get_content: callable = lambda:  _content_interface.subscribe(self._channel, self.rect)

    def draw(self, surface: pygame.Surface) -> None:
        content: pygame.Surface

        try:
            content = self._get_content()
        except Exception as e:
            log(f"[ContentPane] Error retrieving content! {e}")

        self._surface.blit(content, (0, 0))
        surface.blit(self._surface, self.rect.topleft)

    def handle_event(self, event: pygame.event.Event) -> None:
        _content_interface.publish(self._channel, event)



# a UIElement container
class Canvas(UIElement): 
    def __init__(self, rect: pygame.Rect, theme: dict=DEFAULT_THEME):
        super().__init__(rect)
        self.elems: list[UIElement] = []
        self.theme = theme
        self._surface: pygame.Surface = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        self.forwardRelevant: bool = True # if true, only forwards events to relevant children (ie event collision)

    def _add_elem(self, *elems: UIElement) -> None:
        # elems are added relative to the canvas
        for elem in elems:
            self.elems.append(elem)
            
    def _add_elem_top(self, *elems: UIElement) -> None:
        # elems are added relative to the canvas
        for elem in elems:
            self.elems.insert(1, elem)

    def _wipe_elems(self) -> None:
        self.elems.clear()

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type not in MOUSE_EVENTS or not self.interactable:
            return
        
        # relativise event position to local coords
        local_event: pygame.event.Event = localEvent(event, self.rect)

        # handle event for each elem
        elem: UIElement
        for elem in self.elems:
            if elem.interactable:
                if self.forwardRelevant:
                    if elem.rect.collidepoint(local_event.pos):
                        elem.handle_event(local_event)
                else:
                    elem.handle_event(local_event)

    def draw(self, surface: pygame.Surface) -> None:
        # clear local surface and redraw
        self._surface.fill((0,0,0,0))

        elem: UIElement
        for elem in self.elems:
            if elem.visible:
                elem.draw(self._surface)

        surface.blit(self._surface, self.rect.topleft)



class SelectionPane(Canvas):
    def __init__(self, rect: pygame.Rect, multi_select: bool=False):
        super().__init__(rect, DEFAULT_THEME)

        pad: int = 20
        self._add_elem(
            *[Checkbox(
                pygame.Rect(pad, i*45 + pad, self.rect.w - 2*pad, 40),
                f"Checkbox {i}",
                lambda i=i: log(f"Checkbox {i} toggled!"),
                check_type="solid",
            ) for i in range(5)]
        )

        self.handle_event = super().handle_event if multi_select else self.handle_event_single_select

    def draw(self, surface: pygame.Surface) -> None:
        self._surface.fill(DEFAULT_THEME["panel"])

        elem: UIElement
        for elem in self.elems:
            if elem.visible:
                elem.draw(self._surface)

        surface.blit(self._surface, self.rect.topleft)

    def handle_event_single_select(self, event: pygame.event.Event) -> None:
        if event.type not in MOUSE_EVENTS or not self.interactable:
            return
        
        # relativise event position to local coords
        local_event: pygame.event.Event = localEvent(event, self.rect)

        # handle event for each elem
        outputs: list = []
        elem: Checkbox
        for elem in self.elems:
            if elem.interactable:
                outputs.append(elem.handle_event(local_event))
        
        if any(outputs):
            for i, output in enumerate(outputs):
                if output:
                    for j, elem in enumerate(self.elems):
                        elem._render = True
                        if i != j:
                            elem.state = False
                    
                    break

    def get_selected(self) -> list[int]:
        return [i for i, elem in enumerate(self.elems) if isinstance(elem, Checkbox) and elem.state]

# the default header
class Header(Canvas):
    def __init__(self, title: str, rect: pygame.Rect):
        super().__init__(rect)
        self.title: str = title

        self._add_elem(
            Button_Tap(
                rect=pygame.Rect(30, 35, 120, 50),
                text="Home",
                callback=lambda: goto("home")
            ),
        )

    def draw(self, surface: pygame.Surface) -> None:
        pygame.draw.rect(surface, self.theme["panel"], self.rect)
        super().draw(surface)

        # add the page title
        title: pygame.Surface = FONT_LARGE.render(self.title, True, self.theme["text"])
        surface.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, HEADER_HEIGHT // 2)))

        # add the datetime widget
        time_surface: pygame.Surface = get_time_surface()
        surface.blit(
            time_surface,
            time_surface.get_rect(midright=(SCREEN_WIDTH - 30, HEADER_HEIGHT // 2))
        )

# the default footer
class Footer(Canvas):
    def __init__(self, rect: pygame.Rect):
        super().__init__(rect)

        self._add_elem(
            Button_Tap(
                rect=pygame.Rect(self.rect.width - 140, 20, 120, 50),
                text="Settings",
                callback=lambda: goto("settings")
            ),
        )

    def draw(self, surface: pygame.Surface) -> None:
        pygame.draw.rect(surface, self.theme["panel"], self.rect)
        super().draw(surface)

# the default page
class Page(Canvas):
    def __init__(self, title: str, dims: tuple=(SCREEN_WIDTH, SCREEN_HEIGHT)):
        self.rect = pygame.Rect(0, 0, *dims)
        super().__init__(self.rect)
        self.title: str = title

        self._add_elem(
            Header(self.title, pygame.Rect(0, 0, self.rect.width, HEADER_HEIGHT)),
            Footer(pygame.Rect(0, self.rect.height - FOOTER_HEIGHT, self.rect.width, FOOTER_HEIGHT)),
        )

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(DEFAULT_THEME["bg"])
        super().draw(surface)

class TestPage(Page):
    def __init__(self, title: str, dims: tuple=(SCREEN_WIDTH, SCREEN_HEIGHT)):
        super().__init__(title, dims)
        
    
    def handle_event(self, event: pygame.event.Event) -> None:
        super().handle_event(event)

        for child in self.elems:
            if isinstance(child, Checkbox) and child.state:
                log(f"Checkbox '{child.text}' is currently active.")

class Chart(UIElement):
    def __init__(self, rect: pygame.Rect, data: list=None):
        super().__init__(rect)
        self._surface = pygame.Surface(self.rect.size, pygame.SRCALPHA)

        self.data: list[tuple[datetime, float]] = data or []
        self.bg_color: tuple = (0, 0, 0, 0)
        self.line_color: tuple = DEFAULT_THEME["elem"]
        self.point_color: tuple = DEFAULT_THEME["elem_hover"]
        self.padding: int = 20
        self.tick_color: tuple = DEFAULT_THEME["muted"]

    def add_point(self, timestamp: datetime, value: float) -> None:
        self.data.append((timestamp, value))
        self._render = True

    def _compute_points(self) -> list[tuple[int, int]]:
        """Convert time/value pairs into pixel coordinates within the chart surface.

        The points returned are relative to ``(0,0)`` of ``self._surface``; the
        caller will blit the surface at ``self.rect.topleft`` when drawing.
        Coordinates respect the configured ``padding`` inset.
        """
        if not self.data:
            return []

        pts = sorted(self.data, key=lambda t_v: t_v[0])
        times, vals = zip(*pts)
        t0 = times[0]
        t1 = times[-1]
        total = max((t1 - t0).total_seconds(), 1)

        vmin = min(vals)
        vmax = max(vals)
        if vmin == vmax:
            vmax = vmin + 1

        inner_w = self.rect.w - 2 * self.padding
        inner_h = self.rect.h - 2 * self.padding

        points: list[tuple[int, int]] = []
        for t, v in pts:
            x_frac = (t - t0).total_seconds() / total
            x = int(self.padding + x_frac * inner_w)

            y_frac = (v - vmin) / (vmax - vmin)
            y = int(self.padding + (inner_h - (y_frac * inner_h)))

            points.append((x, y))

        return points
    
    def _draw_axes(self) -> None:
        """Draw x/y axes with a few notch ticks."""
        w, h = self.rect.size
        p = self.padding

        # axes lines
        pygame.draw.line(self._surface, self.tick_color, (p, h - p), (w - p, h - p), 1)
        pygame.draw.line(self._surface, self.tick_color, (p, p), (p, h - p), 1)

        # simple ticks: five evenly spaced
        num_ticks = 5
        for i in range(num_ticks + 1):
            # x-axis ticks
            tx = p + i * ((w - 2 * p) / num_ticks)
            pygame.draw.line(self._surface, self.tick_color, (tx, h - p - 3), (tx, h - p + 3), 1)
            # y-axis ticks
            ty = p + i * ((h - 2 * p) / num_ticks)
            pygame.draw.line(self._surface, self.tick_color, (p - 3, ty), (p + 3, ty), 1)

    def rerender(self) -> None:
        self._surface.fill(self.bg_color)
        self._draw_axes()
        pts = self._compute_points()

        if len(pts) >= 2:
            pygame.draw.aalines(self._surface, self.line_color, False, pts)

        for p in pts:
            pygame.draw.circle(self._surface, self.point_color, p, 4)

    def draw(self, surface: pygame.Surface) -> None:
        if self._render:
            self._render = False
            self.rerender()

        surface.blit(self._surface, self.rect.topleft)

    def handle_event(self, event: pygame.event.Event) -> None:
        # this proof‑of‑concept chart does not react to events yet
        self._render = True



outbox: Mailbox = Mailbox()

def goto(page: str) -> None:
    outbox.put(page)
    
def getPage(key: str) -> Page:
    return pages.get(key, HomePage())

def get_time_surface() -> pygame.Surface:
    now = datetime.now().strftime("%A %d %b · %I:%M:%S %p")
    return FONT_SMALL.render(now, True, DEFAULT_THEME["muted"])



goto("home")



if __name__ == "__main__":
    pygame.init()

    SCREEN = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Graphics Test")
    CLOCK = pygame.time.Clock()

    page: Page = TestPage("Test Page", (SCREEN_WIDTH, SCREEN_HEIGHT))

    # simple chart proof-of-concept, generate some fake timestamped data
    from datetime import timedelta
    now = datetime.now()
    sample = [(now + timedelta(seconds=i * 5), i * 3.0 + (i % 2) * 2) for i in range(25)]
    chart = Chart(pygame.Rect(50, 150, 800, 400), data=sample)
    page._add_elem(chart)

    # pane = pygame.Surface((400,300))
    # pane.fill((200,200,200))

    # other = pygame.Surface((100,100))
    # other.fill((100,100,100))

    # other.blit(pane, (50,50))

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

            page.handle_event(event)

        
        page.draw(SCREEN)
        pygame.display.flip()
        CLOCK.tick(50)