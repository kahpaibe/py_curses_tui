import curses
from curses import window as cwin, color_pair as cp
from ..genstr import GenStr


# =====================================
#  Elementary drawing utils
# =====================================
def apply_algebraic_color_pair(window: cwin, color_pair: int) -> None:
    """Apply a color pair (algebraic) to a curses window."""
    if color_pair < 0:
        window.attron(curses.A_REVERSE)
    window.attron(cp(abs(color_pair)))

def remove_color_pair(window: cwin, color_pair: int) -> None:
    """Remove a color pair (algebraic) from a curses window."""
    if color_pair < 0:
        window.attroff(curses.A_REVERSE)
    window.attroff(cp(abs(color_pair)))

def draw_genstr(
    window: cwin, y: int, x: int, genstr: GenStr, default_color_pair: int
) -> None:
    """Draw a generated string.

    Args:
        window (curses.window): The curses window to draw on.
        y (int): The y-coordinate to start drawing.
        x (int): The x-coordinate to start drawing.
        genstr (GenStr): The generated string to draw.
        default_color_pair (int): The default color pair to use for sections of the GenStr that do not specify a color pair.
    """
    drawn_length: int = 0

    for section in genstr:
        text = section.text
        color_pair = (
            section.color_pair if section.color_pair is not None else default_color_pair
        )
        attrs = section.attrs

        apply_algebraic_color_pair(window, color_pair)
        for attr in attrs:
            window.attron(attr)

        try:
            window.addstr(y, x + drawn_length, text)
        except curses.error:
            pass

        remove_color_pair(window, color_pair)
        for attr in attrs:
            window.attroff(attr)

        drawn_length += len(text)


def draw_fill(
    window: cwin, y: int, x: int, h: int, w: int, color_pair: int, char: str = " "
) -> None:
    """Draw a filled rectangle."""
    apply_algebraic_color_pair(window, color_pair)

    for i in range(h):
        try:
            window.hline(y + i, x, char, w)
        except curses.error as e:
            pass

    remove_color_pair(window, color_pair)

def draw_border(
    window: cwin,
    y: int,
    x: int,
    h: int,
    w: int,
    color_pair: int,
    char_horizontal: str = "-",
    char_vertical: str = "|",
    char_corner_top_left: str = "+",
    char_corner_top_right: str = "+",
    char_corner_bottom_left: str = "+",
    char_corner_bottom_right: str = "+",
) -> None:
    """Draw a border around a rectangle."""
    raise NotImplementedError