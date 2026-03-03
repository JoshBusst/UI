from UI.core.UIElements import *
from UI.core import worker
from UI.charting.charts import *
from UI.exampleApp import BasicApp


class ChartNew(Chart):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def draw(self, surface):
        super().draw(surface)
        # self._surface.fill((100,100,100), self._graph_rect())
        # surface.blit(self._surface, self.rect.topleft)

    def handle_event(self, event: pygame.event.Event) -> None:
        super().handle_event(event)

        if event.type in [pygame.MOUSEBUTTONDOWN]:
            local_event: pygame.event.Event = localEvent(event, self.rect)
            if self._graph_rect().collidepoint(local_event.pos):
                print(f"Graph point: {self._graph_point(local_event.pos)}")
                data_point = self.graph_to_data(self._graph_point(local_event.pos))
                if data_point:
                    self.add_point(*data_point)




class TestPage(Page):
    def __init__(self, title: str, dims: tuple=(SCREEN_WIDTH, SCREEN_HEIGHT)):
        super().__init__(title, dims)
        
    
    def handle_event(self, event: pygame.event.Event) -> None:
        super().handle_event(event)

        for child in self.elems:
            if isinstance(child, Checkbox) and child.state:
                log(f"Checkbox '{child.text}' is currently active.")



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
    chart = ChartNew(
        pygame.Rect(50, 150, 800, 400),
        data=sample,
        title="Shit",
        x_label="Time",
        y_label="Value",
        legend=["Sample Data"],
    )
    page._add_elem(chart)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

            page.handle_event(event)

        
        page.draw(SCREEN)
        pygame.display.flip()
        CLOCK.tick(50)