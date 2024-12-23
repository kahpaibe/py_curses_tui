import curses
import curses.ascii
from dataclasses import dataclass, field
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Optional,
    Self,
    SupportsIndex,
    Tuple,
    overload,
)

from ..utility import MAX_DELTA, ColorPair, Point, cp, cwin


# ==== Color palettes ====
@dataclass
class ColorPairs:
    """List of color pairs used by the terminal.
    To use the curses.COLOR_x constants, the ColorPairs object must be defined after curses is initialized.

    Example usage:
        # == in main.py ==
        def get_color_pairs() -> ColorPairs:  # enables definition after curses is initialized
            return ColorPairs(
                pairs=[
                    (curses.COLOR_RED, curses.COLOR_WHITE),  # 1 (Error)
                    (curses.COLOR_WHITE, curses.COLOR_RED),  # 2 (Error inverse)
                    (curses.COLOR_MAGENTA, curses.COLOR_WHITE),  # 3 (Warning)
                    (curses.COLOR_WHITE, curses.COLOR_MAGENTA),  # 4 (Warning)
                    (curses.COLOR_BLUE, curses.COLOR_WHITE),  # 5 (Info)
                    (curses.COLOR_WHITE, curses.COLOR_BLUE),  # 6 (Info)
                    (curses.COLOR_BLACK, curses.COLOR_WHITE),  # 7
                    (curses.COLOR_BLUE, curses.COLOR_BLACK),  # 8
                    (curses.COLOR_WHITE, curses.COLOR_BLUE),  # 9
                    (curses.COLOR_BLACK, curses.COLOR_CYAN),  # 10
                    (curses.COLOR_WHITE, curses.COLOR_BLUE),  # 11
                    (curses.COLOR_WHITE, curses.COLOR_RED),  # 12
                ]
            )

        def main(stdscr):
            color_pairs = get_color_pairs()
            color_palette = ColorPalette()
            ui = UserInterface(stdscr, color_pairs, color_palette) # use the color pairs

        if __name__ == "__main__":
            curses.wrapper(main) # initialize curses
    """

    pairs: List[ColorPair] = field(
        default_factory=list
    )  # starting form id 1 (0 always default color)


@dataclass
class ColorPalette:  # using curses.color_pair
    """Color palette for the Drawable objects.

    Use negative values to use the inverted colors for the pair.

    Example usage, to set a new palette for a given menu:
        palette = ColorPalette(text=8, boxes=9)
        menu2 = Menu(..., palette=palette)"""

    # == General ==
    text: int = 0  # text color
    box: int = 0  # box borders and background
    cursor: int = 8  # current "mouse over" item
    scrollbar: int = 4  # scrollbars
    button_selected: int = -12  # selected button
    button_unselected: int = -16  # unselected button

    button_selected_invalid = -5  # selected button with invalid option
    button_unselected_invalid = 13  # unselected button with invalid option

    box_hover: int = -4  # hover color for boxes
    box_selected: int = 4  # selected color for boxes
    # == Palette for text edit objects ==
    text_edit_text: int = -12  # text in text input objects
    text_edit_inactive: int = -12  # text input objects when not active
    text_edit_full: int = 17  # if line is full
    text_edit_cursor: int = -12  # cursor in text input objects
    text_edit_hover: int = -14  # color when hovering text input without activating it
    # == Palette for file explorer objects ==
    file_explorer_file: int = 0  # file in file explorer
    file_explorer_directory: int = 6  # directory in file explorer
    file_explorer_dots: int = 15  # dot directories (current / parent) in file explorer
    file_explorer_dim: int = 15  # dimmed text for file or directory in file explorer
    file_explorer_selected: int = 15  # selected file or directory name preview in file explorer
    file_explorer_path: int = -16  # path in file explorer
    file_explorer_scrollbar: int = 4  # scrollbar in file explorer
    # == Palette for file explorer prompt (ui.browse_file or ui.browse_directory) ==
    explorer_prompt_file: int = 12  # file or directory in file explorer
    explorer_prompt_directory: int = 13  # directory in file explorer
    explorer_prompt_dots: int = 16  # dot directories (current / parent) in file explorer
    explorer_prompt_dim: int = 16  # dimmed text for file or directory in file explorer
    explorer_prompt_selected: int = 16  # selected file or directory name preview in file explorer
    explorer_prompt_path: int = -15  # path in file explorer
    explorer_prompt_scrollbar: int = 12  # scrollbar in file explorer


@dataclass
class AttrStr:
    """String with attributes.

    color_pair_id: color pair id (None = default color defined in the color palette)

    Example usage:
        text = AttrStr("text", 1, [curses.BOLD])  # text with bold attribute
        text2 = AttrStr("text2", 2, [curses.BOLD])  # text2 with bold attribute
        text3 = AttrStr("text3", 1, [])  # text3 with no attributes"""

    text: str = ""
    color_pair_id: int | None = None
    attributes: List[int] = field(default_factory=list)

    def get_copy(self) -> "AttrStr":
        """Return a copy of the object."""
        return AttrStr(self.text, self.color_pair_id, self.attributes)


class GenStr(List[AttrStr]):
    @overload
    def __init__(self):
        """Construct an empty GenStr object."""
        ...

    @overload
    def __init__(self, iterable: Iterable[AttrStr | str], /):
        """Construct a GenStr object from an iterable of AttrStr or string objects."""
        ...

    @overload
    def __init__(self, *args: AttrStr):
        """Construct a GenStr object from a list of AttrStr objects."""
        ...

    @overload
    def __init__(self, *args: Tuple[str, int | None, List[int]]):
        """Construct a GenStr object from a list of tuples.
        Such tuples define the AttrStr objects in order.

        Some fields are optional, and can be left empty.

        Example:
            gs = GenStr( ("text", 1, []), (" text2", 2, [curses.BOLD]), (" text3") )"""
        ...

    @overload
    def __init__(self, *args: str):
        """Construct a GenStr object from given strings."""
        ...

    @overload
    def __init__(self, genstr: "GenStr"):
        """Construct a GenStr object from a GenStr object (copy)."""

    @overload
    def __init__(self, *args: List[Any], **kwargs: Dict[str, Any]):
        """GenStr should not be initialized with **kwargs."""
        ...

    def __init__(
        self,
        *args: None | str | AttrStr | Tuple[int, int | None, List[int]] | Iterable[AttrStr | str],
        **kwargs: Dict[str, Any],
    ):  # main implementation
        """Construct a GenStr (generalized string) object. Basically a list of AttrStr objects.

        Ways to initialize:
            - empty: GenStr()
            - single argument: GenStr("text") or GenStr("text", 1) or GenStr("text", 1, [curses.BOLD])
            - single iterable argument: GenStr( [AttrStr("text", 1), "text2", AttrStr("text3", 2, [curses.BOLD])] )
            - multiple arguments: GenStr(AttrStr("text", 1), "text2", AttrStr("text3", 2, [curses.BOLD]))
            - from a GenStr object (copy): GenStr( genstr1 )

        No **kwargs are allowed.

        Example:
            gs = GenStr(AttrStr("text", 1), "text2", AttrStr("text3", 2, [curses.BOLD]))
        """
        # stop if kwargs are provided
        if kwargs:
            raise ValueError(
                "GenStr must be initialized with an iterable of AttrStr objects or *args only."
            )

        if len(args) == 0:  # no argument
            super().__init__()
        elif len(args) == 1 and isinstance(args[0], tuple):
            super().__init__()
            self.append(AttrStr(*args[0]))
        elif len(args) == 1 and isinstance(args[0], str):  # single string argument
            super().__init__()
            self.append(AttrStr(args[0]))
        elif len(args) == 1 and isinstance(args[0], GenStr):  # copy
            super().__init__()
            for attr in args[0]:
                self.append(attr.get_copy())
        elif len(args) == 1 and isinstance(args[0], Iterable):  # single iterable argument
            super().__init__()
            for arg in args[0]:
                if isinstance(arg, str):
                    self.append(AttrStr(arg))
                elif isinstance(arg, AttrStr):
                    self.append(arg)
                elif isinstance(arg, tuple):
                    self.append(AttrStr(*arg))
                else:
                    raise ValueError(
                        f"GenStr must be initialized with an iterable of AttrStr, strings or tuple only, not {type(arg)}"
                    )
        else:  # multiple arguments
            super().__init__()
            for arg in args:
                if isinstance(arg, str):
                    self.append(AttrStr(arg))
                elif isinstance(arg, AttrStr):
                    self.append(arg)
                elif isinstance(arg, tuple):
                    self.append(AttrStr(*arg))
                else:
                    raise ValueError(
                        f"GenStr must be initialized with args of type AttrStr, strings or Tuples only, not {type(arg)}"
                    )

    def __str__(self) -> str:
        return self.unfolded()

    def append(self, item: AttrStr) -> None:
        if not isinstance(item, AttrStr):
            raise TypeError(f"Expected instance of AttrStr, got {type(item)}")
        super().append(item)

    def insert(self, index: SupportsIndex, object: AttrStr) -> None:
        if not isinstance(object, AttrStr):
            raise TypeError(f"Expected instance of AttrStr, got {type(object)}")
        return super().insert(index, object)

    @staticmethod
    def unfold(genstr: "GenStr") -> str:
        """Unfold a GenStr object into a string."""
        if isinstance(genstr, str):
            return genstr
        return "".join(attr.text for attr in genstr)

    def unfolded(self) -> str:
        """Get unfolded version of this GenStr object (string)."""
        return self.unfold(self)

    def get_copy(self) -> "GenStr":
        """Return a copy of the object."""
        genstr = GenStr()
        for attr in self:
            genstr.append(attr.get_copy())
        return genstr


# ==== Drawable objects: related structures ====
@dataclass
class Choice:  # A choice
    """A choice for Drawables with choices such as SingleSelect, MultiSelect, Choose or ScrollableChoose.

    text: text to display. If a GenStr object, it will be displayed with multiple colors and attributes.

    For several Drawables using Choice objects, the action may be provided as a self argument.
    Example:
        action = lambda selfo: user_interface.set_value(selfo.text, "")"""

    text: GenStr | str  # (generalized) text to display. Effectively of type GenStr.
    action: Optional[Callable[[Optional["Drawable"]], Any]] = lambda: None

    def __post_init__(self):
        if isinstance(self.text, str):
            self.text = GenStr(self.text)


@dataclass
class Hitbox:
    """Points to determine the 'hitbox' of the KeyCaptureDrawable object"""

    tl: Point = (0, 0)
    br: Point = (0, 0)

    def get_tl(self) -> Point:
        return self.tl

    def get_br(self) -> Point:
        return self.br

    def get_tr(self) -> Point:
        return (self.tl[0], self.br[1])

    def get_bl(self) -> Point:
        return (self.br[0], self.tl[1])

    def get_corners(self) -> Tuple[Point, Point, Point, Point]:
        """Get tl, tr, br, bl corners of the hitbox."""
        return (self.get_tl(), self.get_tr(), self.get_br(), self.get_bl())

    def is_inside(self, p: Point, offset: Point = (0, 0)) -> bool:
        """Return whether a point is inside the hitbox.
        offset: Origin of the Hitbox"""
        y, x = p
        return (
            self.tl[0] + offset[0] <= y <= self.br[0] + offset[0]
            and self.tl[1] + offset[1] <= x <= self.br[1] + offset[1]
        )


# ==== Drawable objects: base classes ====


class Drawable:  # abstract class
    """An object that can be drawn.

    Args:
        y (int): y coordinate (relative if parent given)
        x (int): x coordinate (relative if parent given)
        parent (Drawable, optional): parent in hierarchy (e.g. may be used for relative coordinates).
        palette (ColorPalette, optional): color palette. Defaults to Container's palette if not given.

    on_update:
        Never called.

    custom_data:
        Custom data storage. May be used for various purposes.
    """

    def __init__(
        self,
        y: int,
        x: int,
        parent: Optional["Drawable"] = None,
        palette: Optional[ColorPalette] = None,
    ):
        self.x = x  # always local coordinates
        self.y = y
        self.parent: Drawable | None = parent  # parent in hierarchy (e.g. may be used for movement)
        self._palette = palette  # color palette

        self.on_update: Callable[[Self], Any] | None = (
            None  # Called on respective events. Should be set using .set_on_update(callable)
        )
        self.custom_data: Dict[str, Any] = (
            {}
        )  # Custom data storage. May be used for various purposes.

    def add_custom_data(self, key: str, value: Any) -> None:
        """Add custom data."""
        self.custom_data[key] = value

    def clear_custom_data(self) -> None:
        """Clear all custom data."""
        self.custom_data.clear()

    def get_custom_data(self, key: str) -> Any:
        """Get custom data."""
        if key not in self.custom_data:
            raise KeyError(f"Key '{key}' not found in custom data.")
        return self.custom_data[key]

    def get_yx(self) -> Tuple[int, int]:
        """Retrieves global coordinates (due to parent hierarchy)."""
        if self.parent:
            py, px = self.parent.get_yx()
            return (py + self.y, px + self.x)
        return (self.y, self.x)  # if no parent, local = global coordinates

    def draw(self, window: cwin) -> None:
        """Draw the object."""
        pass

    def key_behaviour(self, key: int):
        """Behaviour of the object on key press."""
        pass

    def set_on_update(self, on_update: Callable[[Self], Any]) -> None:
        """Set the on_update method."""
        self.on_update = on_update

    def set_palette(self, palette: ColorPalette, should_override: bool = True) -> None:
        """Set the color palette. Used for changing the color palette for some objects."""
        if should_override:
            self._palette = palette
        if self.get_palette() is None:
            self._palette = palette


    def get_palette(self) -> ColorPalette:
        """Get the color palette."""
        return self._palette
    
    def _get_palette_bypass(self) -> ColorPalette:
        """Return the color palette used for the init."""
        if self.get_palette() is None:
            return ColorPalette()
        return self.get_palette()

    def __eq__(self, obj: object) -> bool:
        return id(self) == id(obj)

    @staticmethod
    def draw_str(
        text: GenStr,
        window: cwin,
        y: int,
        x: int,
        attributes: List[int] = [curses.A_NORMAL],
        default_pair_id: int = 0,
    ) -> None:
        """Draw given string with given attributes.

        Args:
            text (GenStr): text to draw
            window: window to draw in
            y (int): y coordinate
            x (int): x coordinate
            color_pair_index (int, optional): color pair index. Defaults to 0 = default terminal color pair.
            attributes (List[int], optional): list of attributes to add on top of GenStr attributes. e.g., [curses.A_BOLD, curses.A_ITALIC].
            default_pair_id (int, optional): default color pair id, used if text[k].color_pair_id = 0.

        If color_pair_id is None, the default color pair is used.
        If color_pair_id is negative, the inverted color pair is used.

        About GenStr:
            Generalized strings are used to allow texts to have multiple colors and attributes.
            They are lists of such AttrStr objects, of the form [(string, color_pair_id, attributes), ...]

            e.g.:
                string = "text1"
                color_pair_id = 1
                attributes = [curses.A_BOLD]

        """
        cursor: int = 0
        for attr_str in text:
            t, pair_id, text_attrs = attr_str.text, attr_str.color_pair_id, attr_str.attributes
            inverted = False
            if pair_id is None:
                pair_id = default_pair_id
            if pair_id < 0:  # inverted color
                pair_id = abs(pair_id)
                window.attron(curses.A_REVERSE)
                inverted = True

            for a in attributes:
                window.attron(a)
            for a in text_attrs:
                window.attron(a)

            window.attron(cp(pair_id))

            try:
                window.addstr(y, x + cursor, t)
            except curses.error:
                pass

            window.attroff(cp(pair_id))

            for a in attributes:
                window.attroff(a)
            for a in text_attrs:
                window.attroff(a)
            cursor += len(t)
            if inverted:  # inverted color
                window.attroff(curses.A_REVERSE)
        return

    @staticmethod
    def fill(win: cwin, uly: int, ulx: int, lry: int, lrx: int, pair_id: int = 0) -> None:
        """Fill the area at the provided coordinates of given size"""
        if pair_id < 0:  # if negative, use inverted colors
            win.attron(curses.A_REVERSE)
            win.attron(cp(-pair_id))
            try:
                for y in range(uly, lry + 1):
                    win.hline(y, ulx, " ", lrx - ulx + 1)
            except curses.error:
                pass
            win.attroff(cp(-pair_id))
            win.attroff(curses.A_REVERSE)
        else:
            win.attron(cp(pair_id))
            try:
                for y in range(uly, lry + 1):
                    win.hline(y, ulx, " ", lrx - ulx + 1)
            except curses.error:
                pass
            win.attroff(cp(pair_id))

    @staticmethod
    def rectangle(win: cwin, tl: Tuple[int, int], br: Tuple[int, int], pair_id: int = 0) -> None:
        """Draw a rectangle with the given color pair."""
        uly, ulx = tl
        lry, lrx = br

        def _exception_safe_rectangle():
            try:  # with order which allows to draw the rectangle even if the window is too small
                win.vline(uly + 1, ulx, curses.ACS_VLINE, lry - uly - 1)
                win.hline(uly, ulx + 1, curses.ACS_HLINE, lrx - ulx - 1)
                win.vline(uly + 1, lrx, curses.ACS_VLINE, lry - uly - 1)
                win.addch(uly, ulx, curses.ACS_ULCORNER)
                win.addch(uly, lrx, curses.ACS_URCORNER)
                win.addch(lry, ulx, curses.ACS_LLCORNER)
                win.hline(lry, ulx + 1, curses.ACS_HLINE, lrx - ulx - 1)
                win.addch(lry, lrx, curses.ACS_LRCORNER)
            except curses.error:
                pass

        if pair_id < 0:  # if negative, use inverted colors
            win.attron(curses.A_REVERSE)
            win.attron(cp(-pair_id))
            _exception_safe_rectangle()
            win.attroff(cp(-pair_id))
            win.attroff(curses.A_REVERSE)
        else:
            win.attron(cp(pair_id))
            _exception_safe_rectangle()
            win.attroff(cp(pair_id))

    @staticmethod
    def get_str_fixed_size(text: str, size: int, centered: bool = False) -> str:
        """Return a string of fixed size, possibly centered."""
        if centered:
            if len(text) > size:
                return text[:size]
            else:
                padding = size - len(text)
                left_padding = padding // 2
                right_padding = padding - left_padding
                return " " * left_padding + text + " " * right_padding
        else:
            return f"{text[:size]:<{size}}"

    @staticmethod
    def get_genstr_fixed_size(genstr: GenStr, size: int, centered: bool = False) -> GenStr:
        """Return a GenStr generalized string of fixed size, possibly centered."""
        if centered:
            # Make centered text
            # Calculate the length of text to put in the center

            length = sum(len(s.text) for s in genstr)
            if length == 0:
                return GenStr([AttrStr(" " * size)])
            if length < size:
                padding = size - length
                left_padding = padding // 2
                right_padding = padding - left_padding
                newgenstr = genstr.copy()
                newgenstr.insert(
                    0, AttrStr(" " * left_padding, genstr[0].color_pair_id, genstr[0].attributes)
                )
                newgenstr.append(
                    AttrStr(" " * right_padding, genstr[-1].color_pair_id, genstr[-1].attributes)
                )
                return newgenstr

        # == If not centered or text to center too long ==
        # Calculate current total length of strings
        current_length = sum(len(s.text) for s in genstr)

        truncated_strings = GenStr()
        remaining_length = size

        for s in genstr:
            if len(s.text) <= remaining_length:
                truncated_strings.append(s)
                remaining_length -= len(s.text)
            else:
                truncated_strings.append(
                    AttrStr(
                        s.text[:remaining_length] + " " * (size - current_length),
                        s.color_pair_id,
                        s.attributes,
                    )
                )
                remaining_length = 0
                break

        return truncated_strings

    @staticmethod
    def distance(origin: Tuple[int, int], p: Tuple[int, int], direction: int) -> int:
        """Return the 'distance' from origin to p.
        direction 0: down, 1: right, 2: up, 3: left

        If changes are made, please update Submenu.handle_kcd_goto() accordingly.
        """

        y1, x1 = origin
        y2, x2 = p
        dx, dy = x2 - x1, y2 - y1
        if x1 == x2 and y1 == y2:
            return MAX_DELTA * MAX_DELTA

        elif direction == 0:  # v
            """Order described (example 6x6 with MAX_DELTA = 6):
            31 33 35 25 27 29
            32 34 36 26 28 30
            17 18  1  5  9 13
            19 20  2  6 10 14
            21 22  3  7 11 15
            23 24  4  8 12 16
            """
            if dy > 0 and dx >= 0:  # zone 1 bot right
                sup = 0  # supplement value to get in which zone we are
                return sup + dy + dx * (MAX_DELTA - y1 - 1)
            elif dy > 0 and dx < 0:  # zone 2 bot left
                sup = MAX_DELTA * MAX_DELTA  # supplement value to get in which zone we are
                return sup + (MAX_DELTA - y1 - 1) * (MAX_DELTA - x1) + (dy - 1) * x1 + x2 + 1
            elif dy <= 0 and dx > 0:  # zone 3 top right
                sup = 2 * MAX_DELTA * MAX_DELTA  # supplement value to get in which zone we are
                return sup + (MAX_DELTA - y1 - 1) * MAX_DELTA + (dx - 1) * (y1 + 1) + y2 + 1
            else:  # dy <= 0 and dx <) 0 # zone 4 top left
                sup = 3 * MAX_DELTA * MAX_DELTA  # supplement value to get in which zone we are
                sbot = (MAX_DELTA - y1 - 1) * MAX_DELTA
                return sup + sbot + (y1 + 1) * (MAX_DELTA - x1 - 1) + x2 * (y1 + 1) + y2 + 1

        elif direction == 1:  # >
            """Order described (example 6x6 with MAX_DELTA = 6):
            22 28 34  5  7  9
            23 29 35  4  6  8
            24 30 36  1  2  3
            25 31 19 10 13 16
            26 32 20 11 14 17
            27 33 21 12 15 18
            """
            if dx > 0 and dy == 0:  # zone 1 right
                sup = 0  # supplement value to get in which zone we are
                return sup + dx
            elif dx > 0 and dy < 0:  # zone 2 top right
                sup = MAX_DELTA * MAX_DELTA
                return sup + (y1 - y2) + (dx - 1) * y1
            elif dx > 0 and dy > 0:  # zone 3 bot right
                sup = 2 * MAX_DELTA * MAX_DELTA
                return sup + dy + (dx - 1) * (MAX_DELTA - y1 - 1)
            elif dx == 0 and dy > 0:  # zone 4 just below origin
                sup = 3 * MAX_DELTA * MAX_DELTA
                return sup + dy
            else:  # zone 5 top left
                sup = 4 * MAX_DELTA * MAX_DELTA
                return sup + y2 + x2 * MAX_DELTA

        elif direction == 2:  # ^ reverse of v
            """Order described (example 6x6 with MAX_DELTA = 6):
             6  4  2  8 10 12
             5  3  1  7  9 11
            14 13 36 35 34 33
            20 19 32 31 30 29
            18 17 28 27 26 25
            16 15 24 23 22 21
            """
            if dy < 0 and dx <= 0:  # zone 1 top left
                sup = 0  # supplement value to get in which zone we are
                return sup + (y1) * (x1 - x2) + y1 - y2
            elif dy < 0 and dx > 0:  # zone 2 top right
                sup = MAX_DELTA * MAX_DELTA
                s = (y1) * (x1 + 1)
                return sup + s + (dx - 1) * y1 + y1 - y2
            elif dy == 0 and dx < 0:  # zone 3 just left of origin
                sup = 2 * MAX_DELTA * MAX_DELTA
                s = (y1) * (MAX_DELTA)
                return sup + s + (x1 - x2)
            elif dy > 0 and dx < 0:  # zone 3bis bottom left
                sup = 2 * MAX_DELTA * MAX_DELTA
                s = (y1) * (MAX_DELTA) + x1
                return sup + s + x1 * (MAX_DELTA - y2 - 1) + x1 - x2
            else:  # zone 4 bottom right
                sup = 3 * MAX_DELTA * MAX_DELTA
                s = (y1) * (MAX_DELTA) + (MAX_DELTA - y1) * x1
                return sup + s + (MAX_DELTA - x1) * (MAX_DELTA - y2 - 1) + MAX_DELTA - x2
        elif direction == 3:  # <
            """Order described (example 6x6 with MAX_DELTA = 6):
             9  7  5 34 28 22
             8  6  4 35 29 23
             3  2  1 36 30 24
            16 13 10 19 31 25
            17 14 11 20 32 26
            18 15 12 21 33 27
            """
            if dx < 0 and dy == 0:  # zone 1 left
                sup = 0  # supplement value to get in which zone we are
                return sup + (x1 - x2)
            elif dx < 0 and dy < 0:  # zone 2 top left
                sup = MAX_DELTA * MAX_DELTA
                return sup + (y1 - y2) + y1 * (x1 - x2 - 1)
            elif dx < 0 and dy > 0:  # zone 3 bot left
                sup = 2 * MAX_DELTA * MAX_DELTA
                return sup + (MAX_DELTA - y2 - 1) + (x1 - x2 - 1) * (MAX_DELTA - y1 - 1)
            elif dx == 0 and dy < 0:  # zone 4 just below
                sup = 3 * MAX_DELTA * MAX_DELTA
                return sup + y1 - y2
            else:  # zone 5 top right
                sup = 4 * MAX_DELTA * MAX_DELTA
                return sup + y2 + (MAX_DELTA - x1 - 1) * MAX_DELTA
        else:
            raise ValueError(f"Invalid direction {direction}. " + "Should be in {0,1,2,3}")


class DrawableContainer(Drawable):
    """A generic container for drawables that can be drawn."""

    def __init__(
        self,
        y: int,
        x: int,
        parent: Optional[Drawable] = None,
        palette: Optional[ColorPalette] = None,
    ):
        """Drawable object which can contain drawables.

        on_update:
            Never called."""
        super().__init__(y, x, parent)
        self.drawables: List[Drawable] = []
        self.set_palette(palette, False)

    def draw(self, window: cwin) -> None:
        for obj in self.drawables:
            obj.draw(window)

    def key_behaviour(self, key: int):
        for obj in self.drawables:
            obj.key_behaviour(key)

    def add(self, obj: Drawable, palette: Optional[ColorPalette] = None) -> None:
        if not obj.parent:
            obj.parent = self  # container is parent
        obj.set_palette(palette if palette else self.get_palette(), False) # set palette if not already set
        self.drawables.append(obj)

    def clear(self) -> None:
        self.drawables.clear()


class KeyCaptureDrawable(Drawable):
    """A drawable that captures key behaviour. Menus can thus make it able to switch between them.
    Example children: SingleSelect or TextBox class

    Color palette:
        Unused

    On update:
        Never called"""

    def __init__(self, y: int, x: int, parent: Drawable | None = None):
        super().__init__(y, x, parent)
        # What to call to go to next KeyCaptureDrawable.
        # Often is Menu.handle_capture(origin:(int,int), direction:(int 0-3)), 0:down, 1: right, 2:up, 3:left
        # direction -1: goto previous in column 1: goto next in column, origin = (y,x) cursor origin position
        self.capture_goto: Callable[[Tuple[int, int], int], Any] = None
        # What to call to take over the capture. horizontal_move_y should be the target y for cursor
        # Often would be set to self.__capture_take. Syntax is as follow:
        # def __capture_take(self,origin=(y:int, x:int), direction:int 0-3):
        self.capture_take: Callable[[Self, Tuple[int, int], int], Any] | None = None
        # What to call to remove the capture
        # Often would be set to self.__capture_remove. Syntax is as follow:
        # def ___capture_remove(self, direction:int 0-3):
        self.capture_remove: Callable[[Self, int], Any] | None = None
        self.bypass_if_activated: bool = False  # if activated, bypass key actions such as "q" quit
        self._overwritten_hitbox: bool = False  # if true, the hitbox is manually set

    def distance_from(self, p: Tuple[int, int], direction: int) -> int:
        """Return the 'distance' between this object and a point p.
        direction 0: down, 1: right, 2: up, 3: left"""

        hitbox = self.get_hitbox()
        tl, tr, br, bl = hitbox.get_corners()

        if hitbox.is_inside(p):
            return MAX_DELTA * MAX_DELTA * MAX_DELTA  # if inside, return a big value
        else:
            dist_tl = Drawable.distance(p, tl, direction)
            dist_tr = Drawable.distance(p, tr, direction)
            dist_br = Drawable.distance(p, br, direction)
            dist_bl = Drawable.distance(p, bl, direction)
            return min(dist_tl, dist_tr, dist_br, dist_bl)

    def get_hitbox(self) -> Hitbox:
        """Return hitbox of the object."""
        if self._overwritten_hitbox:
            return self._hitbox
        else:
            raise NotImplementedError("get_hitbox method must be implemented in child class")

    def overwrite_hitbox(self, hitbox: Hitbox, relative: bool = False) -> None:
        """Overwrite the hitbox of the object."""
        self._overwritten_hitbox = True
        if relative:  # if relative coordinates
            y, x = self.get_yx()
            hitbox.tl = (hitbox.tl[0] + y, hitbox.tl[1] + x)
            hitbox.br = (hitbox.br[0] + y, hitbox.br[1] + x)
        self._hitbox = hitbox

    def reset_hitbox(self) -> None:
        """Reset the hitbox of the object."""
        self._overwritten_hitbox = False


class Submenu(Drawable):
    """A submenu that can be drawn, used for smart navigation."""

    def __init__(self):
        """A submenu that can be drawn, used for smart navigation.

        on_update:
            Base on components only."""
        self._tl: Point = (-1, -1)  # top left corner
        self._br: Point = (-1, -1)  # bottom right corner
        self._kcds: List[KeyCaptureDrawable] = []  # KeyCaptureDrawables
        self._selected: int = 0  # selected drawable

        self.capture_goto: Callable[[Point, int], bool] = None  # returns bool success
        self.capture_take: Callable[[KeyCaptureDrawable, Point, int], None] = self._capture_take
        self.capture_remove: Callable[[int], None] = self._capture_remove

        self.custom_data: Dict[str, Any] = (
            {}
        )  # Custom data storage. May be used for various purposes.

    def add_custom_data(self, key: str, value: Any) -> None:
        """Add custom data."""
        self.custom_data[key] = value

    def clear_custom_data(self) -> None:
        """Clear all custom data."""
        self.custom_data.clear()

    def get_custom_data(self, key: str) -> Any:
        """Get custom data."""
        if key not in self.custom_data:
            raise KeyError(f"Key '{key}' not found in custom data.")
        return self.custom_data[key]

    def handle_kcd_goto(self, origin: Point, direction: int) -> None:
        """Handle the capture of the submenu."""
        if self._selected == -1:
            raise ValueError("No drawable selected, should never happend.")

        current_kcd = self._kcds[self._selected]
        # get closest kcd in current submenu
        m = min(
            range(len(self._kcds)), key=lambda i: self._kcds[i].distance_from(origin, direction)
        )
        dist = self._kcds[m].distance_from(origin, direction)
        if direction == 0:  # v down
            if (dist < MAX_DELTA * MAX_DELTA) or (
                dist < 2 * MAX_DELTA * MAX_DELTA
            ):  # zone 1 = bot right/ 2 = bot left
                current_kcd.capture_remove(0)
                self._selected = m  # select it directly
                self._kcds[m].capture_take(origin, 0)
            else:  # zone 3 = top right / 4 = top left
                current_kcd.capture_remove(0)
                # call the Menu to try to change to above submenu
                origin_sub = origin
                success = self.capture_goto(origin_sub, 0)  # try going go up
                if not success:
                    self._selected = m  # select target in current submenu
                    self._kcds[m].capture_take(origin, direction)
        elif direction == 1:  # > right
            if (
                (dist < MAX_DELTA * MAX_DELTA)
                or (dist < 2 * MAX_DELTA * MAX_DELTA)
                or (dist < 3 * MAX_DELTA * MAX_DELTA)
                or (dist < 4 * MAX_DELTA * MAX_DELTA)
            ):  # zone 1 = right / 2 = top right / 3 = bot right / 4 = below
                current_kcd.capture_remove(1)
                self._selected = m  # select it directly
                self._kcds[m].capture_take(origin, 1)
            else:  # zone 3 = top left / 4 = bot left
                current_kcd.capture_remove(1)
                # call the Menu to try to change to above submenu
                origin_sub = origin
                success = self.capture_goto(origin_sub, 1)  # try going go right
                if not success:
                    self._selected = m
                    self._kcds[m].capture_take(origin, direction)
        elif direction == 2:  # ^ up
            if (dist < MAX_DELTA * MAX_DELTA) or (
                dist < 2 * MAX_DELTA * MAX_DELTA
            ):  # zone 1 = top left / 2 = top right
                current_kcd.capture_remove(2)
                self._selected = m  # select it directly
                self._kcds[m].capture_take(origin, direction)
            else:  # zone 3 = bot left / 4 = bot right
                current_kcd.capture_remove(2)
                # call the Menu to try to change to above submenu
                origin_sub = origin
                success = self.capture_goto(origin_sub, 2)  # try going go down
                if not success:
                    self._selected = m
                    self._kcds[m].capture_take(origin, direction)
        elif direction == 3:  # < left
            if (
                (dist < MAX_DELTA * MAX_DELTA)
                or (dist < 2 * MAX_DELTA * MAX_DELTA)
                or (dist < 3 * MAX_DELTA * MAX_DELTA)
                or (dist < 4 * MAX_DELTA * MAX_DELTA)
            ):  # zone 1 = left / 2 = top left / 3 = bot left / 4 = below
                current_kcd.capture_remove(3)
                self._selected = m  # select it directly
                self._kcds[m].capture_take(origin, direction)
            else:  # zone 3 = bot right / 4 = top right
                current_kcd.capture_remove(3)
                # call the Menu to try to change to above submenu
                origin_sub = origin
                success = self.capture_goto(origin_sub, 3)  # try going go left
                if not success:
                    self._selected = m
                    self._kcds[m].capture_take(origin, direction)

    def key_behaviour(self, key: int) -> None:
        """Behaviour of the selected KeyCaptureDrawable on key press."""
        selected = self._selected  # copy
        if len(self._kcds) > 0:
            if not self.should_bypass():  # Add key actions here if needed
                pass
            for i, kcd in enumerate(self._kcds):
                if i == selected:  # only selected key capture drawable
                    kcd.key_behaviour(key)

    def draw(self, window: cwin) -> None:
        for obj in self._kcds:
            obj.draw(window)

    def should_bypass(self) -> bool:
        """Returns whether the current key capture drawable should bypass the key events.
        Example to bypass: "q" to quit the program, etc"""
        try:
            return not self._kcds[self._selected].bypass_if_activated
        except IndexError:
            return False

    def activate(self, index: int) -> None:
        """Select a drawable by index."""
        self._selected = index
        for i in range(len(self._kcds)):
            if i == index:
                self._kcds[i].capture_take((0, 0), 0)
            else:
                self._kcds[i].capture_remove(0)

    def add(self, kcd: KeyCaptureDrawable) -> None:
        """Add a drawable to the submenu."""
        kcd.capture_goto = self.handle_kcd_goto

        self._kcds.append(kcd)
        # update the corners if needed
        kcd_hitbox = kcd.get_hitbox()
        kcd_tl = kcd_hitbox.get_tl()
        kcd_br = kcd_hitbox.get_br()
        if self._tl == (-1, -1):
            self._tl = kcd_tl
            self._br = kcd_br
        if kcd_tl[0] < self._tl[0]:
            self._tl = (kcd_tl[0], self._tl[1])
        if kcd_tl[1] < self._tl[1]:
            self._tl = (self._tl[0], kcd_tl[1])
        if kcd_br[0] > self._br[0]:
            self._br = (kcd_br[0], self._br[1])
        if kcd_br[1] > self._br[1]:
            self._br = (self._br[0], kcd_br[1])

    def clear(self) -> None:
        """Remove all drawables."""
        self._kcds.clear()

    def get_selected_index(self) -> KeyCaptureDrawable:
        """Return the index of the selected drawable."""
        return self._selected

    def get_hitbox(self) -> Hitbox:
        """Return the top left and bottom right corner of the object."""
        tl = self._tl
        br = self._br
        return Hitbox(tl, br)

    def set_hitbox(self, tl: Point, br: Point) -> None:
        """Set the hitbox of the object. Should be used with caution such as creating a Submenu object."""
        self._tl = tl
        self._br = br

    def set_on_update(
        self, on_update: Callable[[Drawable], Any] | None = None, exclude: List[Drawable] = []
    ) -> None:
        """Set the on_update function to all inside kcds. Will skip objects with on_update already define.

        Args:
            on_update (Callable[[Drawable], Any], optional): on_update function. Defaults to None.
            exclude (List[Drawable], optional): list of drawables to exclude. Defaults to []."""
        for kcd in self._kcds:
            if (kcd.on_update is None) and (kcd not in exclude):
                if kcd.on_update is None:
                    kcd.set_on_update(on_update)

    def is_inside(self, p: Point) -> bool:
        """Return whether a point is inside the hitbox."""
        hitbox = self.get_hitbox()
        return hitbox.is_inside(p)

    def distance_from(self, p: Point, direction: int) -> int:
        """Return the 'distance' between this object and a point p.
        direction 0: down, 1: right, 2: up, 3: left"""

        if self.is_inside(p):
            return 4 * MAX_DELTA * MAX_DELTA  # if inside, return a high value
        else:
            hitbox = self.get_hitbox()
            tl, br = hitbox.get_tl(), hitbox.get_br()
            tr, bl = hitbox.get_tr(), hitbox.get_bl()
            # TODO: slow ?
            dist_top = min(
                Drawable.distance(p, (tl[0], i), direction) for i in range(tl[1], tr[1] + 1)
            )
            dist_bottom = min(
                Drawable.distance(p, (br[0], i), direction) for i in range(bl[1], br[1] + 1)
            )
            dist_left = min(
                Drawable.distance(p, (i, tl[1]), direction) for i in range(tl[0], bl[0] + 1)
            )
            dist_right = min(
                Drawable.distance(p, (i, tr[1]), direction) for i in range(tr[0], br[0] + 1)
            )

            return min(dist_top, dist_bottom, dist_left, dist_right)

    @staticmethod
    def _distance_first_point_to_point(origin: Point, p: Point, direction: int) -> int:
        """ "Distance" of kcd to a point p used to get the first kcd to be selected from given direction."""
        oy, ox = origin
        py, px = p
        dy = py - oy
        dx = px - ox

        if direction == 0:  # v down
            s = dy * MAX_DELTA
            return s + dx + 1
        elif direction == 1:  # > right
            s = dx * MAX_DELTA
            return s + dy + 1
        elif direction == 2:  # ^ up
            s = -dy * MAX_DELTA
            return s - dx + 1
        elif direction == 3:  # < left
            s = -dx * MAX_DELTA
            return s + dy + 1
        else:
            raise ValueError(f"Invalid direction {direction}. " + "Should be in {0,1,2,3}")

    @staticmethod
    def _distance_first_kcd(kcd: KeyCaptureDrawable, origin: Point, direction: int) -> int:
        """Distance of kcd to a point p used to get the first kcd to be selected from given direction."""
        hitbox = kcd.get_hitbox()

        if direction == 0:  # v down
            tl = hitbox.get_tl()
            return Submenu._distance_first_point_to_point(origin, tl, direction)
        elif direction == 1:  # > right
            tl = hitbox.get_tl()
            return Submenu._distance_first_point_to_point(origin, tl, direction)
        elif direction == 2:  # ^ up
            br = hitbox.get_br()
            return Submenu._distance_first_point_to_point(origin, br, direction)
        elif direction == 3:  # < left
            tr = hitbox.get_tr()
            return Submenu._distance_first_point_to_point(origin, tr, direction)
        else:
            raise ValueError(f"Invalid direction {direction}. " + "Should be in {0,1,2,3}")

    def find_first(self, p: Point, direction: int) -> int:
        """Return the index of the first KeyCaptureDrawable to be selected from a point p."""

        return min(
            range(len(self._kcds)),
            key=lambda i: Submenu._distance_first_kcd(self._kcds[i], p, direction),
        )

    def _capture_take(self, origin: Point, direction: int) -> None:
        """Takeover the capture."""
        id_ = self.find_first(origin, direction)
        self.activate(id_)

    def _capture_remove(self, direction: int) -> None:
        """Remove the capture."""
        selected_kcd = self._kcds[self._selected]
        selected_kcd.capture_remove(direction)
        self._selected = -1

    def set_palette(self, palette, should_override = True):
        super().set_palette(palette, should_override)
        for kcd in self._kcds:
            kcd.set_palette(palette, should_override)
    