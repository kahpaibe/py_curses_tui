import curses
from curses import window as cwin, color_pair as cp
from typing import Callable

from ..genstr import GenStr


# =====================================
#  Elementary drawing utils
# =====================================
def apply_algebraic_color_pair(window: cwin, color_pair: int) -> None:
    """Apply a color pair (algebraic) to a curses window."""
    if color_pair < 0:
        window.attron(curses.A_REVERSE)
    window.attron(cp(abs(color_pair)))


def remove_algebraic_color_pair(window: cwin, color_pair: int) -> None:
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

        remove_algebraic_color_pair(window, color_pair)
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

    remove_algebraic_color_pair(window, color_pair)


def draw_border(
    window: cwin,
    y: int,
    x: int,
    h: int,
    w: int,
    color_pair: int,
    char_horizontal: str | None = None,
    char_vertical: str | None = None,
    char_corner_top_left: str | None = None,
    char_corner_top_right: str | None = None,
    char_corner_bottom_left: str | None = None,
    char_corner_bottom_right: str | None = None,
) -> None:
    """Draw a border (not filled).
    
    Args:
        window (curses.window): The curses window to draw on.
        y (int): The y-coordinate to start drawing.
        x (int): The x-coordinate to start drawing.
        h (int): The height of the border.
        w (int): The width of the border.
        color_pair (int): The color pair to use for the border (algebraic).
        char_horizontal (str | None): The character to use for horizontal lines. If None, uses curses.ACS_HLINE.
        char_vertical (str | None): The character to use for vertical lines. If None, uses curses.ACS_VLINE.
        char_corner_top_left (str | None): The character to use for the top-left corner. If None, uses curses.ACS_ULCORNER.
        char_corner_top_right (str | None): The character to use for the top-right corner. If None, uses curses.ACS_URCORNER.
        char_corner_bottom_left (str | None): The character to use for the bottom-left corner. If None, uses curses.ACS_LLCORNER.
        char_corner_bottom_right (str | None): The character to use for the bottom-right corner. If None, uses curses.ACS_LRCORNER.
    """
    if h < 2 or w < 2:
        raise ValueError(
            f"Height and width must be at least 2 to draw a border, got {h=}, {w=}."
        )

    apply_algebraic_color_pair(window, color_pair)

    calls: list[tuple[Callable, tuple, dict]] = [  # To be wrapped in try: except
        # Corners
        (window.addch, (y, x, curses.ACS_ULCORNER if char_corner_top_left is None else char_corner_top_left), {}),
        (window.addch, (y, x + w - 1, curses.ACS_URCORNER if char_corner_top_right is None else char_corner_top_right), {}),
        (window.addch, (y + h - 1, x, curses.ACS_LLCORNER if char_corner_bottom_left is None else char_corner_bottom_left), {}),
        (window.addch, (y + h - 1, x + w - 1, curses.ACS_LRCORNER if char_corner_bottom_right is None else char_corner_bottom_right), {}),
        # Top and bottom borders
        (window.hline, (y, x + 1, curses.ACS_HLINE if char_horizontal is None else char_horizontal, w - 2), {}),
        (window.hline, (y + h - 1, x + 1, curses.ACS_HLINE if char_horizontal is None else char_horizontal, w - 2), {}),
        # Left and right borders
        (window.vline, (y + 1, x, curses.ACS_VLINE if char_vertical is None else char_vertical, h - 2), {}),
        (window.vline, (y + 1, x + w - 1, curses.ACS_VLINE if char_vertical is None else char_vertical, h - 2), {}),
    ]

    for func, args, kwargs in calls:
        try:
            func(*args, **kwargs)  # Wrapped call
        except curses.error:
            pass

    remove_algebraic_color_pair(window, color_pair)


def draw_rectangle(
    window: cwin,
    y: int,
    x: int,
    h: int,
    w: int,
    color_pair: int,
    char_fill: str = " ",
    char_horizontal: str | None = None,
    char_vertical: str | None = None,
    char_corner_top_left: str | None = None,
    char_corner_top_right: str | None = None,
    char_corner_bottom_left: str | None = None,
    char_corner_bottom_right: str | None = None,
):
    """Draw a filled rectangle with a border."""
    if h < 2 or w < 2:
        raise ValueError(
            f"Height and width must be at least 2 to draw a rectangle, got {h=}, {w=}."
        )

    inside_h, inside_w = h - 2, w - 2
    if inside_h > 0 and inside_w > 0:
        draw_fill(window, y + 1, x + 1, inside_h, inside_w, color_pair, char_fill)

    draw_border(
        window,
        y,
        x,
        h,
        w,
        color_pair,
        char_horizontal,
        char_vertical,
        char_corner_top_left,
        char_corner_top_right,
        char_corner_bottom_left,
        char_corner_bottom_right,
    )
