import pygame
from pygame.transform import rotate as rotate_surf
from datetime import datetime
from abc import ABC, abstractmethod
from copy import copy

from .worker import log, Mailbox
from .worker import content_interface as _content_interface
from .graphics import *


pygame.init()



# ---------- Mouse Button ----------
MOUSE_BUTTON_LEFT: int = 1
MOUSE_BUTTON_MID: int = 2
MOUSE_BUTTON_RIGHT: int = 3
MOUSE_EVENTS: tuple = (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION)





# ---------- UI Element Primitive ----------
class UIElement(ABC):
    def __init__(self, rect: tuple):
        self.rect: pygame.Rect = pygame.Rect(*rect)
        self._surface: pygame.Surface = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        self.theme: Theme = copy(DEFAULT_THEME)

        self.rerender: bool = True
        self.interactable: bool = True
        self.visible: bool = True
        self.angle: float = 0

        self.set_angle(self.angle)
    
    def set_angle(self, angle: float) -> None:
        self.angle = angle
        self._surface = rotate_surf(self._surface, self.angle)
        self.rect = self._surface.get_rect(center=self.rect.center)

    def localEvent(self, event: pygame.event.Event) -> pygame.event.Event:
        """Relativise an event position to a local rect."""
        if event.type == pygame.MOUSEMOTION:
            return pygame.event.Event(event.type, {
                'pos': (event.pos[0] - self.rect.x, event.pos[1] - self.rect.y),
                'rel': event.rel,
                'buttons': event.buttons,
            })
        else:
            return pygame.event.Event(event.type, {
                'pos': (event.pos[0] - self.rect.x, event.pos[1] - self.rect.y),
                'button': event.button,
            })

    def draw(self, surface: pygame.Surface) -> None:
        # if self.rerender:
        #     self.rerender = False
        #     self.render()
        self.render()
        
        if self.visible:
            surface.blit(self._surface, self.rect)

    @abstractmethod
    def render(self) -> None:
        pass

    @abstractmethod
    def handle_event(self, event: pygame.event.Event) -> None:
        pass



# ---------- Button Primitives ----------
class Button(UIElement):
    """A toggle button. State is toggled on each click, and button is visually depressed while active."""

    def __init__(self, rect: tuple, text: str="", callback: callable=None):
        super().__init__(rect)

        self.theme: Theme = copy(BUTTON_DEFAULT_THEME)
        self._anim_rect: pygame.Rect = self.rect.copy() # used for animation
        self._callback: callable = callback
        self._pressed: bool = False
        self._mouse_hover: bool = False

        self.text: str = text
        self.state: bool = False
    
    def render(self) -> None:
        self._anim_rect = self.rect.copy()
        colour: tuple

        if self._pressed:
            colour = self.theme.elem_pressed
            self._anim_rect = self._anim_rect.move(0, 4)
        elif self.state:
            colour = self.theme.elem_clicked
            self._anim_rect = self._anim_rect.move(0, 2)
        elif self._mouse_hover:
            colour = self.theme.elem_hover
        else:
            colour = self.theme.elem

        # render button background and label text
        pygame.draw.rect(self._surface, colour, pygame.Rect(0,0, *self._anim_rect.size), border_radius=14)
        textSurface: pygame.Surface = self.theme.font.render(self.text, True, self.theme.text)

        self._surface.blit(textSurface, textSurface.get_rect(center=self._surface.get_rect().center))

    def draw(self, surface: pygame.Surface) -> None:
        # if self.rerender:
        #     self.rerender = False
        self.render()
        
        if self.visible:
            surface.blit(self._surface, self._anim_rect.topleft)

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

        self._render = True
        return False

class Button_Tap(Button):
    """A quick-tap button variant. State is not toggled, and button is only visually depressed while held."""

    def __init__(self, rect: tuple, text: str="", callback: callable=None):
        super().__init__(rect, text, callback)

    def handle_event(self, event: pygame.event.Event) -> None:
        super().handle_event(event)

        if self.state:
            self.state = False

class Checkbox(Button):
    def __init__(self, rect: tuple, text: str="", callback: callable=None, check_type: str="tick"):
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

        # self.box_colour: tuple = (0,0,0)
        # self.check_colour: tuple = (0,0,0)
        # self.text_colour: tuple = (0,0,0)
        # self.font: pygame.font.Font = font

    def render(self) -> None:
        """Render an animated checkbox surface."""

        size = self.rect.h - self.box_padding
        surface = pygame.Surface((size, size), pygame.SRCALPHA)

        # --- Draw check mark ---
        if self.state:
            if self.check_type in self._type_renders:
                self._type_renders[self.check_type](surface, size, self.theme.border)
            else:
                log(f"Unknown checkbox type '{self.check_type}'! Defaulting to tick.")
                self._type_renders["tick"](surface, size, self.theme.border)
        
        # --- Scale values ---
        border_width = max(2, size // 12)

        # --- render outer box ---
        pygame.draw.rect(
            surface,
            self.theme.border,
            pygame.Rect(0, 0, size, size),
            border_width,
            border_radius=size // 8,
        )

        # render checkbox
        self._surface.fill(self.theme.elem)
        pad: int = (self.rect.height - size) // 2
        self._surface.blit(surface, (pad,pad))
        
        # render display text
        textSurface: pygame.Surface = self.theme.font.render(self.text, True, self.theme.text)
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
    def __init__(self, rect: tuple, text: str=""):
        super().__init__(rect)

        self.theme: Theme = copy(DEFAULT_LABEL_THEME)
        self.text: str = text

    def render(self) -> None:
        self._surface.fill(self.theme.bg)
        pygame.draw.rect(self._surface, (200,200,200,100), self.rect, width=2)

        label: pygame.Surface = self.theme.font.render(self.text, True, self.theme.text)
        self._surface.blit(label, label.get_rect(center=(self.rect.w // 2, self.rect.h // 2)))

    def handle_event(self, event: pygame.event.Event) -> None:
        pass

class Label_anim(Label):
    def __init__(self, rect: tuple, get_text: callable):
        super().__init__(rect, get_text())

        self.get_text: callable = get_text
        self.theme.font = pygame.font.SysFont("segoeui", 16)

    def render(self) -> None:
        self.text = self.get_text()
        super().render()

# a dynamic content pane. Points to a mailbox for content collection
class ContentPane(UIElement):
    def __init__(self, rect: tuple, channel: str):
        super().__init__(rect)

        self._channel: str = channel
        self._get_content: callable = lambda: _content_interface.subscribe(self._channel, self.rect)

    def render(self) -> None:
        try:
            self._surface.blit(self._get_content(), (0, 0))
        except Exception as e:
            log(f"[ContentPane] Error retrieving content! {e}")

    def handle_event(self, event: pygame.event.Event) -> None:
        _content_interface.publish(self._channel, event)



# a UIElement container
class Canvas(UIElement): 
    def __init__(self, rect: tuple):
        super().__init__(rect)

        self.theme.bg = (0,0,0,0) # transparent for canvas, by default
        self.elems: list[UIElement] = []
        self.forwardRelevant: bool = False # if true, only forwards events to relevant children (ie event collision)

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
        local_event: pygame.event.Event = self.localEvent(event)

        # handle event for each elem
        elem: UIElement
        for elem in self.elems:
            if elem.interactable:
                if self.forwardRelevant:
                    if elem.rect.collidepoint(local_event.pos):
                        elem.handle_event(local_event)
                else:
                    elem.handle_event(local_event)

    def render(self) -> None:
        # by default, draws blank background
        self._surface.fill(self.theme.bg)

        elem: UIElement
        for elem in self.elems:
            elem.draw(self._surface)



class SelectionPane(Canvas):
    def __init__(self, rect: tuple, multi_select: bool=False):
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

    def handle_event_single_select(self, event: pygame.event.Event) -> None:
        if event.type not in MOUSE_EVENTS or not self.interactable:
            return
        
        # relativise event position to local coords
        local_event: pygame.event.Event = self.localEvent(event)

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

    def render(self) -> None:
        self._surface.fill(self.theme.panel)

        elem: UIElement
        for elem in self.elems:
            elem.draw(self._surface)

# the default header
class Header(Canvas):
    def __init__(self, title: str, rect: tuple):
        super().__init__(rect)
        self.title: str = title
        self.forwardRelevant = False

        self.theme.bg = self.theme.panel
        self._add_elem(
            Button_Tap(
                rect=(30, 35, 120, 50),
                text="Home",
                callback=lambda: goto("home"),
            ),
            Label_anim(
                (self.rect.width - 240, 20, 220, 80),
                get_text=lambda: datetime.now().strftime("%A %d %b · %I:%M:%S %p"),
            ),
            Label(
                (0, 0, self.rect.width, self.rect.height),
                title,
            )
        )

# the default footer
class Footer(Canvas):
    def __init__(self, rect: tuple):
        super().__init__(rect)
        self.forwardRelevant = False
        self.theme.bg = self.theme.panel

        self._add_elem(
            Button_Tap(
                rect=pygame.Rect(self.rect.width - 140, 20, 120, 50),
                text="Settings",
                callback=lambda: goto("settings")
            ),
        )

# the default page
class Page(Canvas):
    def __init__(self, title: str, dims: tuple):
        super().__init__((0,0,*dims))

        self.theme.bg = DEFAULT_THEME.bg
        self.title: str = title
        self._add_elem(
            Header(self.title, (0, 0, self.rect.width, HEADER_HEIGHT)),
            Footer((0, self.rect.height - FOOTER_HEIGHT, self.rect.width, FOOTER_HEIGHT)),
        )



# ==================== PAGE MANAGER ====================
class PageManager:
    def __init__(self, pages: dict[str, Canvas]=None, default_page: str=None):
        self.pages: dict[str, Canvas] = pages or {}
        self.current: str = default_page if default_page in self.pages else None

        self.back_stack: list[str] = []
        self.forward_stack: list[str] = []
        self.forward_down: bool = True

        if self.current is None and self.pages:
            self.current = next(iter(self.pages))

    def add_page(self, key: str, page: Canvas) -> None:
        self.pages[key] = page

        if self.current is None:
            self.set_page(key)

    def set_page(self, key: str) -> None:
        if key == self.current or key == None:
            return  # don't pollute history

        if page not in self.pages.keys():
            log("[PageManager] set_page: Input key does not exist!")
            return # dont allow invalid names
        
        self.back_stack.append(self.current)
        self.forward_stack.clear()
        print(f"Page changed: {self.current} -> {key}")
        self.current = key

    def go_back(self) -> None:
        if not self.back_stack:
            return

        self.forward_stack.append(self.current)
        self.current = self.back_stack.pop()

    def go_forward(self) -> None:
        if not self.forward_stack:
            return

        self.back_stack.append(self.current)
        self.current = self.forward_stack.pop()

    def current_page(self) -> Canvas:
        return self.pages.get(self.current, None)

    def handle_event(self, event: pygame.event) -> None:
        # Keyboard navigation
        if event.type == pygame.KEYDOWN:
            mods = pygame.key.get_mods()

            if mods & pygame.KMOD_ALT:
                if event.key == pygame.K_LEFT:
                    self.go_back()
                elif event.key == pygame.K_RIGHT:
                    self.go_forward()

        if self.forward_down and self.current_page():
            self.current_page().handle_event(event)

    def draw(self, surface: pygame.Surface) -> None:
        if self.current_page():
            self.current_page().draw(surface)



outbox: Mailbox = Mailbox()

def goto(page: str) -> None:
    outbox.put(page)
    
def get_time_surface() -> pygame.Surface:
    now = datetime.now().strftime("%A %d %b · %I:%M:%S %p")
    return DEFAULT_THEME.font.render(now, True, DEFAULT_THEME.muted)





if __name__ == "__main__":
    SCREEN_WIDTH, SCREEN_HEIGHT = (900,900)

    pygame.init()

    SCREEN = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Graphics Test")
    CLOCK = pygame.time.Clock()

    page: Page = Page("Test Page", (SCREEN_WIDTH, SCREEN_HEIGHT))


    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

            page.handle_event(event)

        
        page.draw(SCREEN)
        pygame.display.flip()
        CLOCK.tick(50)