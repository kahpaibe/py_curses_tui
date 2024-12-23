import curses
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


class MultiSelect(KeyCaptureDrawable):
    """A list of choices, with multiple choices selectable at a time."""

    unsel = "[ ]"  # unselected symbol
    sel = "[*]"  # selected symbol

    def __init__(
        self,
        y: int,
        x: int,
        choices: list[Choice],
        palette: Optional[ColorPalette] = None,
        parent: Drawable | None = None,
    ):
        """A list of choices, with multiple choices selectable at a time.

        Args:
            y (int): y coordinate
            x (int): x coordinate
            choices (list[Choice]): list of choices
            palette (ColorPalette, optional): color palette. Defaults to None.
            parent (Drawable, optional): parent in hierarchy (e.g. may be used for relative coordinates).

        Color palette:
            text: color of the text.
            cursor: color of the selected text.

        On update:
            Called when:
                multi_select.add_choice() is called.
                multi_select.clear_choices() is called.
                multi_select.set_selected() is called.
                toggleling an item.
            Suppressed before first draw.

        The Choice.action action may be provided with a self argument.
        Example:
            choice1.action = lambda selfo: print(selfo.selected) # where selfo is the MultiSelect object
        """
        super().__init__(y, x, parent)
        self._height = len(choices)

        self._choices = choices
        self._selected = []  # selected choices
        self._cursor = -1  # cursor ("mouse" over) position # starting at -1 not that bad !
        self.set_palette(palette, False) # None if not set, should be overwritten when adding to a container
        self.capture_take = self._capture_take
        self.capture_remove = self._capture_remove

        self._first_draw = False  # whether it was drawn once. Sort of init

    def add_choice(self, choice: Choice) -> None:
        """Add a choice to the list.

        Args:
            choice (Choice): choice to add

        The Choice.action action may be provided with a self argument.
        Example:
            choice1.action = lambda selfo: print(selfo.selected) # where selfo is the MultiSelect object
        """
        self._choices.append(choice)

        if self._first_draw:  # suppress before first draw
            if self.on_update:
                try_self_call(self, self.on_update)

    def clear_choices(self) -> None:
        """Clear all choices."""
        self._choices.clear()
        self._selected.clear()
        self._cursor = -1

        if self._first_draw:  # suppress before first draw
            if self.on_update:
                try_self_call(self, self.on_update)

    def get_choices(self) -> List[Choice]:
        """Get all choices"""
        return self._choices

    def get_selected_indexes(self) -> List[int]:
        """Get current selected choices indexes."""
        return self._selected
    
    def get_selected_choices(self) -> List[Choice]:
        """Get current selected choices."""
        return [self._choices[i] for i in self._selected]

    def get_selected_index(self) -> List[int]:
        """Return the indexes of the selected choices."""
        return self._selected

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
        if len(self._choices) == 0:  # if empty
            if self._cursor == -1:
                Drawable.draw_str(GenStr(" "), window, y, x, [], self._get_palette_bypass().text)
            else:  # hover
                Drawable.draw_str(GenStr(" "), window, y, x, [], self._get_palette_bypass().cursor)
            return

        for i, choice in enumerate(self._choices):

            gs = GenStr(f"{self.sel if i in self._selected else self.unsel} ")
            gs += choice.text

            if i == self._cursor:
                Drawable.draw_str(
                    gs,
                    window,
                    i + y,
                    x,
                    [curses.A_BOLD],
                    self._get_palette_bypass().cursor,
                )
            else:
                Drawable.draw_str(
                    gs,
                    window,
                    i + y,
                    x,
                    [],
                    self._get_palette_bypass().text,
                )

    def key_behaviour(self, key: int) -> None:
        if len(self._choices) == 0:  # if empty
            self._key_behaviour_empty(key)
            return

        if key == curses.KEY_UP:
            self._cursor = self._cursor - 1
            if self._cursor < 0:
                if self.capture_goto:
                    y, x = self.get_yx()
                    origin = (y + self._cursor + 1, x)
                    self.capture_goto(origin, 2)  # goto previous
                else:
                    self._cursor = self._cursor % len(self._choices)
        elif key == curses.KEY_DOWN:
            self._cursor = self._cursor + 1
            if self._cursor >= len(self._choices):
                if self.capture_goto:
                    y, x = self.get_yx()
                    origin = (y + len(self._choices) - 1, x)
                    self.capture_goto(origin, 0)  # goto next
                else:
                    self._cursor = self._cursor % len(self._choices)
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
            if self._cursor in self._selected:
                self._selected.remove(self._cursor)
            else:
                self._selected.append(self._cursor)
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
                origin = (y, x)
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
        if len(self._choices) == 0:  # if empty
            self._cursor = 0
            return

        sy, sx = self.get_yx()
        miny, maxy = sy, sy + len(self._choices) - 1
        oy, ox = origin

        if direction == 0:  # from up to down
            self._cursor = 0
        elif direction == 2:  # from down to up
            self._cursor = len(self._choices) - 1
        elif direction == 1 and (sx < ox):  # -> but wrong direction
            self._cursor = 0
        elif direction == 3 and (sx > ox):  # <- but wrong direction
            self._cursor = len(self._choices) - 1
        else:
            if oy > maxy:
                self._cursor = len(self._choices) - 1
            elif oy < miny:
                self._cursor = 0
            else:
                self._cursor = oy - sy  # set cursor to same y value

    def _capture_remove(self, direction: int) -> None:
        """Remove the capture.
        direction 0: down, 1: right, 2: up, 3: left"""
        self._cursor = -1

    def get_hitbox(self) -> Hitbox:
        """Return hitbox of the object."""
        if self._overwritten_hitbox:
            return self._hitbox
        elif len(self._choices) == 0:  # if empty
            y, x = self.get_yx()
            return Hitbox((y, x), (y, x))
        else:
            y, x = self.get_yx()
            w = max(len(c.text) for c in self._choices)
            return Hitbox((y, x), (y + len(self._choices) - 1, x + w - 1))
