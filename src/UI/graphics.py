from numpy import rec
import pygame
from datetime import datetime
from abc import ABC, abstractmethod
from .worker import log, Mailbox, _content_interface



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
FONT_SMALL = pygame.font.SysFont("segoeui", 18)
FONT_MED = pygame.font.SysFont("segoeui", 24)
FONT_LARGE = pygame.font.SysFont("segoeui", 34, bold=True)

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


# the base UIElement class
class UIElement(ABC):
    def __init__(self, rect: pygame.Rect):
        self.rect: pygame.Rect = rect
        self.interactable: bool = True
        self.visible: bool = True

    @abstractmethod
    def draw(self, surface: pygame.Surface) -> None:
        pass

    @abstractmethod
    def handle_event(self, event: pygame.event.Event) -> None:
        pass

# a clickable button
class Button(UIElement):
    def __init__(self, rect: pygame.Rect, text: str="", callback: callable=None):
        super().__init__(rect)

        self.anim_rect: pygame.Rect = rect.copy() # used for animation
        self.text: str = text
        self.callback: callable = callback

        self.pressed: bool = False
        self.mouse_hover: bool = False

    def draw(self, surface: pygame.Surface) -> None:
        self.rect = self.anim_rect

        if self.pressed:
            colour = DEFAULT_THEME["elem_pressed"]
            self.rect = self.anim_rect.move(0, 2)
        elif self.mouse_hover:
            colour = DEFAULT_THEME["elem_hover"]
        else:
            colour = DEFAULT_THEME["elem"]

        pygame.draw.rect(surface, colour, self.rect, border_radius=14)

        label = FONT_MED.render(self.text, True, DEFAULT_THEME["elem_text"])
        surface.blit(label, label.get_rect(center=self.rect.center))

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type not in [pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION]:
            return
        
        if self.anim_rect.collidepoint(event.pos):
            self.mouse_hover = True

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == MOUSE_BUTTON_LEFT:
                self.pressed = True

            elif event.type == pygame.MOUSEBUTTONUP and event.button == MOUSE_BUTTON_LEFT and self.pressed:
                self.pressed = False
                self.callback()
        else:
            self.mouse_hover = False
            self.pressed = False

# a clickable button
class ButtonSolidState(Button):
    def __init__(self, rect: pygame.Rect, text: str=""):
        super().__init__(rect, text=text)

        self.callback: callable = self.toggleState
        self.state: bool = False
    
    def draw(self, surface: pygame.Surface) -> None:
        self.rect = self.anim_rect

        if self.pressed:
            colour = DEFAULT_THEME["elem_pressed"]
            self.rect = self.anim_rect.move(0, 4)
        elif self.state:
            colour = DEFAULT_THEME["elem_clicked"]
            self.rect = self.anim_rect.move(0, 2)
        elif self.mouse_hover:
            colour = DEFAULT_THEME["elem_hover"]
        else:
            colour = DEFAULT_THEME["elem"]

        pygame.draw.rect(surface, colour, self.rect, border_radius=14)

        label = FONT_MED.render(self.text, True, DEFAULT_THEME["elem_text"])
        surface.blit(label, label.get_rect(center=self.rect.center))

    def toggleState(self) -> None:
        self.state = not self.state


class Checkbox(UIElement):
    def __init__(self, rect: pygame.Rect):
        super().__init__(rect)

        self.anim_rect: pygame.Rect = self.rect.copy()
        self.checked: bool = False
        self.pressed: bool = False
        self.mouse_hover: bool = False
        self.surface: pygame.Surface = pygame.Surface(self.rect.size, pygame.SRCALPHA)

    def draw(self, surface: pygame.Surface) -> None:
        self.rect = self.anim_rect

        self.surface.fill((255, 255, 255))
        pygame.draw.rect(
            self.surface,
            (0, 0, 0),
            self.surface.get_rect(),
            3,
        )

        # depress slightly when clicked
        if self.pressed:
            self.anim_rect.move(0,2)

        if self.checked:
            padding = self.rect.h // 4
            pygame.draw.line(
                self.surface,
                (0, 0, 0),
                (padding, self.rect.h // 2),
                (self.rect.h // 2 - 2, self.rect.h - padding),
                3,
            )
            pygame.draw.line(
                self.surface,
                (0, 0, 0),
                (self.rect.h // 2 - 2, self.rect.h - padding),
                (self.rect.h - padding, padding),
                3,
            )

            # pygame.draw.rect(boxSurf, (100,100,100), self.rect, border_radius=14)
        # label = FONT_MED.render(self.text, True, DEFAULT_THEME["elem_text"])
        # surface.blit(label, label.get_rect(center=self.rect.center))

        surface.blit(self.surface, self.rect.topleft)

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
        local_event: pygame.event.Event

        if event.type == pygame.MOUSEMOTION:
            local_event = pygame.event.Event(event.type, {
                'pos': (event.pos[0] - self.rect.x, event.pos[1] - self.rect.y),
                'rel': event.rel,
                'buttons': event.buttons,
            })
        else:
            local_event = pygame.event.Event(event.type, {
                'pos': (event.pos[0] - self.rect.x, event.pos[1] - self.rect.y),
                'button': event.button,
            })

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



# the default header
class Header(Canvas):
    def __init__(self, title: str, rect: pygame.Rect):
        super().__init__(rect)
        self.title: str = title

        self._init_contents()

    def _init_contents(self) -> None:
        self._add_elem(
            Button(
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
        self._init_contents()

    def _init_contents(self) -> None:
        self._add_elem(
            Button(
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
    def __init__(self, title: str):
        self.rect = pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)
        super().__init__(self.rect)
        self.title: str = title

        self._init_contents()

    def _init_contents(self) -> None:
        self._add_elem(
            Header(self.title, pygame.Rect(0, 0, self.rect.width, HEADER_HEIGHT)),
            Footer(pygame.Rect(0, self.rect.height - FOOTER_HEIGHT, self.rect.width, FOOTER_HEIGHT)),
        )

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(DEFAULT_THEME["bg"])
        super().draw(surface)



# ==================== PAGES ====================
class HomePage(Page):
    def __init__(self):
        super().__init__("Home")

        margin: int = 90
        gap: int = 40
        top: int = 60 + HEADER_HEIGHT
        w: int = (SCREEN_WIDTH - margin * 2 - gap) // 2
        h: int = 210

        self._add_elem(
            Button(rect=pygame.Rect(margin, top, w, h), text="Drills", callback=lambda: goto("drills")),
            Button(rect=pygame.Rect(margin + w + gap, top, w, h), text="Analytics", callback=lambda: goto("analytics")),
            Button(rect=pygame.Rect(margin, top + h + gap, w, h), text="Explore", callback=lambda: goto("explore")),
            Button(rect=pygame.Rect(margin + w + gap, top + h + gap, w, h), text="Engine", callback=lambda: goto("engine")),
        )

class DrillsPage(Page):
    def __init__(self):
        super().__init__("Drills")

        pad: int = 30
        height: int = SCREEN_HEIGHT - HEADER_HEIGHT - FOOTER_HEIGHT - pad * 2
        rect: pygame.Rect = pygame.Rect(pad, HEADER_HEIGHT + pad, SCREEN_WIDTH - pad * 2, height)

        self._add_elem(
            ContentPane(rect=rect, channel="BASIC_APP"),
        )

class AnalyticsPage(Page):
    def __init__(self):
        super().__init__("Analytics")

        self._add_elem(
            # ButtonSolidState(rect=pygame.Rect(200,200,50,50)),
        )

class ExplorePage(Page):
    def __init__(self):
        super().__init__("Explore")

class EnginePage(Page):
    def __init__(self):
        super().__init__("Engine")
    
class SettingsPage(Page):
    def __init__(self):
        super().__init__("Settings")



outbox: Mailbox = Mailbox()

def goto(page: str) -> None:
    outbox.put(page)
    
def getPage(key: str) -> Page:
    return pages.get(key, HomePage())

def get_time_surface() -> pygame.Surface:
    now = datetime.now().strftime("%A %d %b · %I:%M:%S %p")
    return FONT_SMALL.render(now, True, DEFAULT_THEME["muted"])


pages: dict[str, Page] = {
    "home": HomePage(),
    "drills": DrillsPage(),
    "analytics": AnalyticsPage(),
    "explore": ExplorePage(),
    "engine": EnginePage(),
    "settings": SettingsPage(),
}

goto("home")


if __name__ == "__main__":
    pygame.init()

    SCREEN = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Training App")
    CLOCK = pygame.time.Clock()

    pane = pygame.Surface((400,300))
    pane.fill((200,200,200))

    other = pygame.Surface((100,100))
    other.fill((100,100,100))

    other.blit(pane, (50,50))

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

        
        SCREEN.blit(other, (100,100))
        pygame.display.flip()
        CLOCK.tick(50)