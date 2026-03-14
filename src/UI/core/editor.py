
from UI.core.UIElements import *

from dataclasses import dataclass
from typing import Any



SCREEN_WIDTH, SCREEN_HEIGHT = (900, 900)



class PropertyElem(Canvas):
    def __init__(self, rect: tuple, name: str, type: str, value: str):
        super().__init__(rect)

        w1: int = self.rect.w*0.15
        w2: int = self.rect.w*0.35
        w3: int = self.rect.w*0.50
        self._add_elem(
            Label((0, 0, w1, self.rect.h), name),
            Label((w1, 0, w2, self.rect.h), type),
            Label((w1 + w2, 0, w3, self.rect.h), value),
        )

class PropertySheet(Canvas):
    def __init__(self, rect: tuple, target: object):
        super().__init__(rect)
        
        elems: list[str] = inspect_class(target)
        h: int = 25

        for i, elem in enumerate(elems):
            print(elem.visibility)
            if elem.visibility == "public":
                self._add_elem(
                    PropertyElem((0,h*i,self.rect.w,h), elem.name, elem.type_name, str(elem.value))
                )
    


@dataclass
class PropertyInfo:
    name:       str
    visibility: str   # public | protected | private
    # kind:       str   # instance var | class var | property | method | classmethod | staticmethod
    type_name:  str
    value:      Any

    def __repr__(self):
        val = repr(self.value)
        if len(val) > 50:
            val = val[:47] + "..."
        return f"{self.name:<30} {self.visibility:<10} {self.type_name:<14} {val}"

def inspect_class(obj: object) -> list[PropertyInfo]:
    cls = type(obj)
    results = []
    seen = set()

    def visibility(name: str) -> str:
        if name.startswith(f"_{cls.__name__}__"):
            return "private"
        
        if name.startswith("_"):
            return "protected"
        
        return "public"

    def kind(name: str, raw: Any) -> str:
        if isinstance(raw, classmethod):   return "classmethod"
        if isinstance(raw, staticmethod):  return "staticmethod"
        if isinstance(raw, property):      return "property"
        if callable(raw):                  return "method"
        if name in vars(cls):              return "class var"

        return "instance var"

    # Walk MRO (reversed = base first, so subclass overrides win)
    for klass in reversed(cls.__mro__):
        for name, raw in vars(klass).items():
            if name in seen or (name.startswith("__") and name.endswith("__")):
                continue
            seen.add(name)

            try:
                value = (raw.fget(obj) if isinstance(raw, property)
                         else getattr(obj, name))
            except Exception:
                value = "<unresolvable>"

            results.append(PropertyInfo(
                name       = name,
                visibility = visibility(name),
                # kind       = kind(name, raw),
                type_name  = type(value).__name__,
                value      = value,
            ))

    results.sort(key=lambda p: (
        {"public": 0, "protected": 1, "private": 2}[p.visibility],
        {"instance var": 0, "class var": 1, "property": 2, "method": 3, "classmethod": 4, "staticmethod": 5},
        p.name
    ))
    return results

def print_class(obj: object) -> None:
    props = inspect_class(obj)

    header = f"{'Name':<30} {'Visibility':<10} {'Kind':<16} {'Type':<14} Value\n"
    header += "─" * len(header)
    print(header)

    section = None
    for p in props:
        if p.visibility != section:
            section = p.visibility
            print(f"\n  {section.upper()}")
        print(f"  {p}")





if __name__ == "__main__":
    pygame.init()

    SCREEN = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Graphics Test")
    CLOCK = pygame.time.Clock()

    page1: Page = Page("Page 1", (SCREEN_WIDTH, SCREEN_HEIGHT))
    page1._add_elem(
        PropertySheet(
            (20, HEADER_HEIGHT + 20, 800, 500),
            Page,
        )
    )

    # exit()

    manager: PageManager = PageManager({
        "page1": page1,
    })

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

            manager.handle_event(event)

        manager.draw(SCREEN)
        pygame.display.flip()
        CLOCK.tick(50)