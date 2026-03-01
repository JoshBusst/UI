
from datetime import datetime
import pygame
import sys

from UI.graphics import FONT_SMALL
from UI.worker import Application



pygame.init()

CLOCK = pygame.time.Clock()
APP_SCREEN_WIDTH = 400
APP_SCREEN_HEIGHT = 400



class BasicApp(Application):
    def __init__(self):
        super().__init__(channel="BASIC_APP", waitOnInactive=True)

    def draw(self, screen: pygame.Surface) -> None:
        draw(screen)

    def handle_event(self, event: pygame.event.Event) -> None:
        handle_event(event)



def handle_event(event: pygame.event.Event) -> None:
    if event.type == pygame.QUIT:
        pygame.quit()
        sys.exit()
    
    if event.type in [pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION]:
        print(f"[App] Received event: {event}!")
        
def draw(screen: pygame.Surface) -> None:
    screen.fill((100,100,100))

    # add the page title
    title: pygame.Surface = FONT_SMALL.render("An Application!", True, (248, 246, 240))
    screen.blit(title, title.get_rect(topleft=(20, 40)))

    # add the datetime widget
    now = datetime.now().strftime("%A %d %b · %I:%M:%S %p")
    time_surf: pygame.Surface = FONT_SMALL.render(now, True, (248, 246, 240))
    screen.blit(
        time_surf,
        time_surf.get_rect(midright=(APP_SCREEN_WIDTH - 30, 80))
    )






if __name__ == "__main__":
    SCREEN = pygame.display.set_mode((APP_SCREEN_WIDTH, APP_SCREEN_HEIGHT))
    pygame.display.set_caption("Sub-app")

    event: pygame.event.Event

    while True:
        # event: pygame.Event = plugin.subscribe_event()
        for event in pygame.event.get():
            handle_event(event)
            
        draw(SCREEN)
        pygame.display.flip()
        CLOCK.tick(50)
