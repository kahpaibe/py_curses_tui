import curses
from curses import window as cwin, color_pair as cp
from ..genstr import GenStr


# =====================================
#  Elementary drawing utils
# =====================================
def draw_genstr(window: cwin, y: int, x: int, genstr: GenStr) -> None:
    """Draw a generated string."""
    drawn_length: int = 0

    for section in genstr:
        text = section.text
        color = section.color
        attr = section.attr

        if color is not None:
            window.attron(cp(color))
        if attr is not None:
            window.attron(attr)

        try:
            window.addstr(y, x + drawn_length, text)
        except curses.error:
            pass

        if color is not None:
            window.attroff(cp(color))
        if attr is not None:
            window.attroff(attr)

        drawn_length += len(text)


def draw_fill(
    window: cwin, y: int, x: int, h: int, w: int, char: str = " ", color_pair: int = 0
) -> None:
    """Draw a filled rectangle."""
