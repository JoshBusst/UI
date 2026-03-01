from abc import ABC, abstractmethod
import pygame
from threading import Lock, Thread, Event
from queue import Queue, Empty as EmptyException, Full as FullException



MAX_EVENT_SIZE: int = 20



def log(message: str) -> None:
    print(f"[Log] {message}")



# thread-safe single-item mailbox
class Mailbox:
    def __init__(self):
        self.value = None
        self.lock = Lock()
    
    def put(self, item):
        """Store the latest item (overwrites previous)"""
        with self.lock:
            self.value = item
    
    def get(self):
        """Get the most recent item"""
        with self.lock:
            return self.value
        
    def clear(self):
        """Clear the mailbox"""
        with self.lock:
            self.value = None



# allows contnet creators to plug into the interface, thread-safe and self-registering
class ContentPlugin:
    channel: str
    _mailbox: Mailbox
    _events_queue: Queue

    def __init__(self, channel: str):
        self.channel = channel
        self._mailbox = Mailbox()
        self._events_queue = Queue(MAX_EVENT_SIZE)

        _content_interface.register(self)


    # Consumer API
    def publish_event(self, event: pygame.event.Event) -> None:
        try:
            self._events_queue.put(event, block=False)
        except FullException:
            pass
        
    def subscribe(self) -> pygame.Surface:
        return self._mailbox.get()


    # Creator API
    def subscribe_event(self, wait: bool=False, timeout: float=0) -> pygame.event.Event:
        try:
            return self._events_queue.get(block=wait, timeout=timeout)
        except EmptyException:
            return None

    def publish(self, surface: pygame.Surface) -> None:
        self._mailbox.put(surface)

# the content bus that manages thread-safe content distribution
class ContentInterface:
    _creators: dict[str, ContentPlugin]
    _running: bool 

    def __init__(self):
        self._creators = {}

    def register(self, creator: ContentPlugin) -> None:
        if creator.channel in self._creators:
            raise ValueError(f"Channel '{creator.channel}' already registered")
        
        self._creators[creator.channel] = creator

    def subscribe(self, channel: str, panel_rect: pygame.Rect) -> pygame.Surface:
        creator: ContentPlugin = self._creators.get(channel)

        if not creator:
            return self._fallback_surface("Content channel inactive!", panel_rect.size)
        
        surface: pygame.Surface = creator.subscribe()
        if not surface:
            return self._fallback_surface("Creator has published no content!")
        
        return surface
    
    def publish(self, channel: str, *events: pygame.event.Event) -> None:
        creator: ContentPlugin = self._creators.get(channel)

        if not creator:
            return None
        
        for event in events:
            try:
                creator._events_queue.put(event, block=False)
            except FullException:
                pass
        
    def _fallback_surface(self, msg: str, size: tuple=(400,400)) -> pygame.Surface:
        surface = pygame.Surface(size)
        surface.fill((50, 50, 50))

        font = pygame.font.SysFont("arial", 24)
        text_surface = font.render(msg, True, (200, 200, 200))
        text_rect = text_surface.get_rect(center=(size[0] // 2, size[1] // 2))

        surface.blit(text_surface, text_rect)

        return surface

# application base class. Includes threading and content plugin interface
class Application(ABC):
    def __init__(self, channel: str, waitOnInactive: bool=False, size: tuple=(400,400), timeout: int=5):
        self._running = False
        self._thread: Thread = None
        self._waitOnInactive: bool = waitOnInactive
        self._timeout: int = timeout
        self._frame_rate: int = 50

        self._plugin: ContentPlugin = ContentPlugin(channel)
        self._size: tuple = size
        self._CLOCK: pygame.time.Clock = pygame.time.Clock()

    def _run(self) -> None:
        screen: pygame.Surface = pygame.Surface(self._size)

        while self._running:
            self.update(screen)
            self._CLOCK.tick(self._frame_rate)

    def start(self) -> None:
        log("[Application] Booting application...")

        self._running: bool = True
        self._thread: Thread = Thread(
            target=self._run,
            daemon=True
        )
        self._thread.start()

    def stop(self) -> None:
        log("[Application] Application exiting...")

        self._running: bool = False

        if self._thread:
            self._thread.join()
            self._thread = None

    def update(self, screen: pygame.Surface) -> None:
        event: pygame.Event = self._plugin.subscribe_event(wait=self._waitOnInactive, timeout=self._timeout)
        
        if event:
            self.handle_event(event)
        elif self._waitOnInactive:
            log(f"No events received in the last {self._timeout} seconds, redrawing...")

        self.draw(screen)
        self._plugin.publish(screen)

    @abstractmethod
    def handle_event(self, event: pygame.event.Event) -> None:
        pass
    
    @abstractmethod
    def draw(self, screen: pygame.Surface) -> None:
        pass





_content_interface = ContentInterface()