import curses
from math import floor
from typing import List, Optional, Tuple

from ..utility import cwin, try_self_call
from .base_classes import (
    Choice,
    ColorPalette,
    Drawable,
    GenStr,
    Hitbox,
    KeyCaptureDrawable,
)


# ==== Drawable objects: props ====
class ScrollableMultiSelect(KeyCaptureDrawable):
    """A list of items that can be scrolled through the user can choose from, choosing executes given action."""

    unsel = "[ ]"  # unselected symbol
    sel = "[*]"  # selected symbol

    arrow_up = "^"  # up arrow symbol
    arrow_down = "v"  # down arrow symbol
    scrollbar = "┃"  # scrollbar symbol # alt █

    def __init__(
        self,
        y: int,
        x: int,
        height: int,
        choices: list[Choice],
        palette: Optional[ColorPalette] = ColorPalette(),
        scroll_type: int = 0,
        parent: Drawable | None = None,
    ):
        """A list of items that can be scrolled through the user can choose from, choosing executes given action.

        Args:
            y: y position.
            x: x position.
            height: height of the list.
            choices: list of choices.
            palette: color palette.
            scroll_type: 0: no scroll, 1: scrollbar, 2: arrows.
            parent: optional parent drawable.

        Color palette:
            text: color of the text.
            cursor: color of the selected text.
            scrollbar: color of the scrollbar.

        on_update:
            Called when:
                scrollable_choose.add_choice() is called.
                scrollable_choose.clear_choices() is called.
            Supressed before first draw.


        The Choice.action action may be provided with a self argument.
        Example:
            choice1.action = lambda selfo: print(selfo.choices) # where selfo is the ScrollableChoose object
        """
        super().__init__(y, x, parent)
        self._height = height
        self._choices = choices
        self._selected = []  # selected choices
        self._cursor = -1  # cursor ("mouse" over) position # starting at -1 not that bad !
        self._scroll_type = scroll_type
        self.palette = palette

        self.capture_take = self._capture_take
        self.capture_remove = self._capture_remove

        self._scroll = 0  # scroll position

        self._first_draw = False  # whether it was drawn once. Sort of init

    def add_choice(self, choice: Choice) -> None:
        """Add a choice to the list.

        Args:
            choice (Choice): choice to add

        The Choice.action action may be provided with a self argument.
        Example:
            choice1.action = lambda selfo: print(selfo.choices) # where selfo is the ScrollableChoose object
        """
        self._choices.append(choice)

        if self._first_draw:  # supressed before first draw
            if self.on_update:
                try_self_call(self, self.on_update)

    def clear_choices(self) -> None:
        """Clear all choices."""
        self._choices.clear()
        self._cursor = -1
        self._scroll = 0
        self._selected.clear()

        if self._first_draw:  # supressed before first draw
            if self.on_update:
                try_self_call(self, self.on_update)

    def get_choices(self) -> list[Choice]:
        """Get all choices"""
        return self._choices

    def get_selected_indexes(self) -> List[Choice]:
        """Get current selected choices indexes."""
        return self._selected

    def current_choice_index(self) -> int:
        """Return the index of the current selected choice (cursor)."""
        return self._cursor + self._scroll

    def set_selected(self, selected: List[int]) -> None:
        """Set the selected choices."""
        self._selected = selected

        if self._first_draw:  # suppress before first draw
            if self.on_update:
                try_self_call(self, self.on_update)

    def draw(self, window: cwin) -> None:
        if not self._first_draw:
            self._first_draw = True
        y, x = self.get_yx()

        if len(self._choices) > 0:
            for i in range(0, self._height):
                if i + self._scroll >= len(self._choices):
                    break
                choice = self._choices[i + self._scroll]
                gs = GenStr(f"{self.sel if i + self._scroll in self._selected else self.unsel} ")
                gs += choice.text
                xf = x + 1 + len(self.arrow_up)
                yf = y + i
                if i == self._cursor:
                    Drawable.draw_str(gs, window, yf, xf, [curses.A_BOLD], self.palette.cursor)
                else:
                    Drawable.draw_str(gs, window, yf, xf, [], self.palette.text)
            if self._scroll_type == 2:  # draw scroll indications
                if self._scroll > 0:  # arrows
                    Drawable.draw_str(GenStr(self.arrow_up), window, y, x, [], self.palette.text)
                if self._scroll < len(self._choices) - self._height:
                    Drawable.draw_str(
                        GenStr(self.arrow_down),
                        window,
                        y + self._height - 1,
                        x,
                        [],
                        self.palette.text,
                    )
            elif self._scroll_type == 1 and len(self._choices) > 1:  # scrollbar
                scrollbar_height = int(
                    max(1, floor(self._height / len(self._choices) * self._height))
                )
                if scrollbar_height < self._height:  # only if enough items
                    scrollbar_y_f = (
                        (self._height - scrollbar_height)
                        / (len(self._choices) - self._height)
                        * self._scroll
                    )

                    if scrollbar_y_f > 0 and round(scrollbar_y_f) == 0:
                        scrollbar_y = 1
                    elif (
                        scrollbar_y_f < self._height - scrollbar_height
                        and round(scrollbar_y_f) == self._height - scrollbar_height
                    ):
                        scrollbar_y = self._height - scrollbar_height - 1
                    else:
                        scrollbar_y = round(scrollbar_y_f)

                    for yf in range(y, self._height + y):
                        Drawable.draw_str(
                            GenStr(
                                " " * len(self.scrollbar)
                                if (
                                    yf < y + scrollbar_y or yf >= y + scrollbar_y + scrollbar_height
                                )
                                else self.scrollbar
                            ),
                            window,
                            yf,
                            x,
                            [],
                            self.palette.scrollbar,
                        )

        else:  # empty
            if self._cursor == -1:
                Drawable.draw_str(GenStr(" "), window, y, x, [], self.palette.text)
            else:  # hover
                Drawable.draw_str(GenStr(" "), window, y, x, [], self.palette.cursor)

    def key_behaviour(self, key: int) -> None:
        if len(self._choices) == 0:
            self._key_behaviour_empty(key)
            return

        if key == curses.KEY_UP:
            if (self.capture_goto and self._cursor <= 0 and self._scroll <= 0) or (
                len(self._choices) == 0
            ):  # if empty
                y, x = self.get_yx()
                origin = (y + self._cursor - 1, x)
                self.capture_goto(origin, 2)  # goto previous
            elif self._cursor > 0:
                self._cursor -= 1
            elif self._cursor <= 0 and self._scroll > 0:
                self._scroll -= 1
                self._cursor = 0
            else:
                self._cursor = (self._cursor - 1) % min(self._height, len(self._choices))

        elif key == curses.KEY_DOWN:
            maxc = self._height - 1
            maxs = len(self._choices) - maxc - 1
            if (
                self.capture_goto
                and self._cursor == min(maxc, len(self._choices) - 1)
                and self._scroll >= maxs
                or len(self._choices) == 0
            ):
                h = min(self._height, len(self._choices))
                y, x = self.get_yx()
                origin = (y + h - 1, x)
                self.capture_goto(origin, 0)  # goto next
            elif self._cursor < maxc:
                self._cursor = (self._cursor + 1) % min(self._height, len(self._choices))
            elif self._cursor >= self._height - 1 and self._scroll < maxs:
                self._scroll += 1
            else:
                self._cursor = (self._cursor + 1) % min(self._height, len(self._choices))
        elif key == curses.KEY_LEFT:
            if self.capture_goto:
                y, x = self.get_yx()
                origin = (y + self._cursor, x)
                self.capture_goto(origin, 3)  # goto left
        elif key == curses.KEY_RIGHT:
            if self.capture_goto:
                y, x = self.get_yx()
                w = max(len(c.text) for c in self._choices)
                origin = (y + self._cursor, x + w - 1)
                self.capture_goto(origin, 1)  # goto right
        elif key == ord("\n"):
            if (
                self._cursor + self._scroll >= 0
                and self._choices[self._cursor + self._scroll].action
            ):

                if self._cursor in self._selected:
                    self._selected.remove(self._cursor + self._scroll)
                else:
                    self._selected.append(self._cursor + self._scroll)

                if self.on_update:
                    try_self_call(self, self.on_update)

    def _key_behaviour_empty(self, key: int) -> None:
        """if empty"""
        if key == curses.KEY_UP:
            if self.capture_goto:
                y, x = self.get_yx()
                origin = (y, x)
                self.capture_goto(origin, 2)  # goto previous=
        elif key == curses.KEY_DOWN:
            if self.capture_goto:
                y, x = self.get_yx()
                origin = (y + self._height, x)
                self.capture_goto(origin, 0)  # goto next
        elif key == curses.KEY_LEFT:
            if self.capture_goto:
                y, x = self.get_yx()
                origin = (y, x)
                self.capture_goto(origin, 3)  # goto left
        elif key == curses.KEY_RIGHT:
            if self.capture_goto:
                y, x = self.get_yx()
                origin = (y, x)
                self.capture_goto(origin, 1)  # goto right

    def _capture_take(self, origin: Tuple[int, int], direction: int) -> None:
        """Takeover the capture.
        origin = (y,x), coordinates of the origin cursor"""
        # 0:down, 1: right, 2:up, 3:left
        if len(self._choices) == 0:
            self._cursor = 0
            self._scroll = 0
            return

        sy, sx = self.get_yx()
        miny, maxy = sy, sy + self._height - 1
        oy, ox = origin

        if direction == 0:  # from up to down
            self._scroll = 0
            self._cursor = 0
        elif direction == 2:  # from down to up
            self._cursor = min(self._height - 1, len(self._choices) - 1)
            self._scroll = max(len(self._choices) - self._height, 0)
        elif direction == 1 and (sx < ox):  # -> but wrong direction
            self._scroll = 0
            self._cursor = 0
        elif direction == 3 and (sx > ox):  # <- but wrong direction
            self._cursor = min(self._height - 1, len(self._choices) - 1)
            self._scroll = max(len(self._choices) - self._height, 0)
        else:
            if oy > maxy:
                self._cursor = min(self._height - 1, len(self._choices) - 1)
                self._scroll = max(len(self._choices) - self._height, 0)
            elif oy < miny:
                self._scroll = 0
                self._cursor = 0
            else:
                self._cursor = oy - sy  # set cursor to same y value, don't change scroll
                if self._cursor < 0:  # failsafe if hitbox is not correct
                    self._cursor = 0
                elif self._cursor >= min(self._height, len(self._choices)):
                    self._cursor = max(min(self._height, len(self._choices)) - 1, 0)

    def _capture_remove(self, direction: int) -> None:
        """Remove the capture.
        direction 0: down, 1: right, 2: up, 3: left"""
        self._cursor = -1

    def get_hitbox(self) -> Hitbox:
        """Return hitbox of the object."""
        if self._overwritten_hitbox:
            return self._hitbox
        elif len(self._choices) == 0:
            y, x = self.get_yx()
            return Hitbox((y, x), (y + self._height, x))
        else:
            y, x = self.get_yx()
            w = max(len(c.text) for c in self._choices)
            h = min(self._height, len(self._choices))
            return Hitbox((y, x), (y + h - 1, x + w - 1))
