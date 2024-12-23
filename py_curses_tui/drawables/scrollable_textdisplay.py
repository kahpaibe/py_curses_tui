import curses
from math import floor
from typing import Optional, Tuple

from ..utility import cwin, try_self_call
from .base_classes import (
    ColorPalette,
    Drawable,
    GenStr,
    Hitbox,
    KeyCaptureDrawable,
)


# ==== Drawable objects: props ====
class ScrollableTextDisplay(KeyCaptureDrawable):
    """Text that can be scrolled through but not edited."""

    arrow_up = "^ "  # up arrow symbol
    arrow_down = "v "  # down arrow symbol
    scrollbar_v = "┃"  # vertical scrollbar symbol
    # scrollbar_h = "━"  # horizontal scrollbar symbol # TODO: add ?

    def __init__(
        self,
        y: int,
        x: int,
        height: int,
        width: int,
        text: str = "",
        scroll_type: int = 0,
        palette: Optional[ColorPalette] = None,
        parent: Drawable | None = None,
    ):
        """An item box that can be scrolled through and edited.
        Warning: it is a complex objects, bugs are likely to appear (hopefully not).

        Args:
            y: y position.
            x: x position.
            height: height of the box.
            width: width of the box.
            text: text to display. Defaults to "".
            scroll_type: 0: no scroll, 1: scrollbar, 2: arrows. Defaults to 0.
            palette: color palette. Defaults to None.
            parent: optional parent drawable.

        Color palette:
            text_edit_text: color of the text.
            text_edit_inactive: color of the text when unfocused.
            text_edit_hover: color of the text when hovered.
            text_edit_cursor: color of the cursor.
            text_edit_full: color of the text when cursor is out of bound.
            scrollbar: color of the arrows or scrollbar.

        on_update:
            Called when:
                scrollable_textdisplay.set_text() is called.
                scrollable_textdisplay.clear_text() is called.
            Supressed before first draw.

        Supported keys: #TODO: update docstr
            - printable characters : write character at cursor position
            - backspace : delete selected character
            - delete : delete next character
            - left arrow : move left
            - right arrow : move right
            - up arrow : move up
            - down arrow : move down
            - shift + left arrow (begin) : move to beginning of the box
            - shift + right arrow (end) : move to end of the box
            - enter : new line / insert line
            - ESC : quit the text box"""

        super().__init__(y, x, parent)
        self._height, self._width = height, width  # maximum width and height
        self._texts = ""
        self._first_draw = False  # whether it was drawn once. Sort of init
        self.set_text(text)
        self._scroll_type = scroll_type
        self.set_palette(palette, False) # None if not set, should be overwritten when adding to a container

        self.capture_take = self._capture_take
        self.capture_remove = self._capture_remove

        self._scroll_y = 0  # vertical scroll position
        self._scroll_x = 0  # horizontal scroll position

        self._state: int = -1  # state of the text box -1: unfocused, 0: hover, 1: active
        self.bypass_if_activated = False  # ignore q press to quit the program, and such inputs

    def set_text(self, text: str) -> None:
        """Set the text in the text box."""
        self._texts = text.split("\n")

        if self._first_draw:  # supressed before first draw
            if self.on_update:
                try_self_call(self, self.on_update)

    def clear_text(self) -> None:
        self.set_text("")

        if self._first_draw:  # supressed before first draw
            if self.on_update:
                try_self_call(self, self.on_update)

    def get_text(self) -> str:
        """Get the text in the text box."""
        return self._texts.join("\n")

    def draw(self, window: cwin) -> None:
        if not self._first_draw:
            self._first_draw = True
        y, x = self.get_yx()
        sx = self._scroll_x  # sy =  self._scroll_y
        # j = self._current_col
        if len(self._texts) > 0:
            xf = x + len(self.arrow_up)
            if self._state == -1:  # unfocused
                for i in range(len(self._texts), self._height):  # Draw background
                    gs = GenStr(" " * self._width)
                    Drawable.draw_str(gs, window, y + i, xf, [], self._get_palette_bypass().text_edit_inactive)
                for i in range(0, min(self._height, len(self._texts))):
                    line = self._texts[i + self._scroll_y]
                    yf = y + i
                    dl = Drawable.get_str_fixed_size(line[sx:], self._width)
                    gs = GenStr(dl)
                    Drawable.draw_str(gs, window, yf, xf, [], self._get_palette_bypass().text_edit_inactive)
            elif self._state == 0:  # hover
                for i in range(len(self._texts), self._height):  # draw background
                    Drawable.draw_str(
                        GenStr(" " * self._width),
                        window,
                        y + i,
                        xf,
                        [],
                        self._get_palette_bypass().text_edit_hover,
                    )
                for i in range(0, min(self._height, len(self._texts))):
                    line = self._texts[i + self._scroll_y]
                    yf = y + i
                    dl = Drawable.get_str_fixed_size(line[sx:], self._width)
                    gs = GenStr(dl)
                    Drawable.draw_str(gs, window, yf, xf, [], self._get_palette_bypass().text_edit_hover)

            else:  # active
                for i in range(len(self._texts), self._height):  # draw background
                    Drawable.draw_str(
                        GenStr(" " * self._width),
                        window,
                        y + i,
                        xf,
                        [],
                        self._get_palette_bypass().text_edit_text,
                    )
                for i in range(0, min(self._height, len(self._texts))):
                    line = self._texts[i + self._scroll_y]
                    yf = y + i
                    dl = Drawable.get_str_fixed_size(line[sx:], self._width)
                    gs = GenStr(dl)
                    Drawable.draw_str(gs, window, yf, xf, [], self._get_palette_bypass().text_edit_text)

            if self._scroll_type == 2:  # draw scroll indications
                if self._scroll_y > 0:  # arrows
                    Drawable.draw_str(
                        GenStr(self.arrow_up), window, y, x, [], self._get_palette_bypass().scrollbar
                    )
                if self._scroll_y < len(self._texts) - self._height:
                    Drawable.draw_str(
                        GenStr(self.arrow_down),
                        window,
                        y + self._height - 1,
                        x,
                        [],
                        self._get_palette_bypass().scrollbar,
                    )
            elif self._scroll_type == 1 and len(self._texts) > 1:  # scrollbar
                scrollbar_height = int(
                    max(1, floor(self._height / len(self._texts) * self._height))
                )
                if scrollbar_height < self._height:  # only if enough items
                    scrollbar_y_f = (
                        (self._height - scrollbar_height)
                        / (len(self._texts) - self._height)
                        * self._scroll_y
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
                                " " * len(self.scrollbar_v)
                                if (
                                    yf < y + scrollbar_y or yf >= y + scrollbar_y + scrollbar_height
                                )
                                else self.scrollbar_v
                            ),
                            window,
                            yf,
                            x,
                            [],
                            self._get_palette_bypass().scrollbar,
                        )

    def key_behaviour(self, key: int) -> None:
        if self._state == -1 or self._state == 1:  # if unfocused, object not as capture
            self._key_behaviour_active(key)
        else:
            self._key_behaviour_hover(key)

    def _key_behaviour_hover(self, key: int) -> None:
        if key in [ord("\n"), curses.KEY_F2]:  # Activate box
            self.activate()
        elif key == curses.KEY_DOWN:
            if self.capture_goto:
                self._state = -1
                y, x = self.get_yx()
                self.capture_goto((y + self._height - 1, x), 0)
        elif key == curses.KEY_UP:
            if self.capture_goto:
                self._state = -1
                origin = self.get_yx()
                self.capture_goto(origin, 2)
        elif key == curses.KEY_LEFT:
            if self.capture_goto:
                self._state = -1
                origin = self.get_yx()
                self.capture_goto(origin, 3)
        elif key == curses.KEY_RIGHT:
            if self.capture_goto:
                self._state = -1
                y, x = self.get_yx()
                self.capture_goto((y, x + self._width - 1), 1)

    def _key_behaviour_active(self, key: int) -> None:
        inw, inh = max([len(k) for k in self._texts] + [0]), len(self._texts)
        smx = inw - self._width
        smy = inh - self._height
        if key in [curses.ascii.ESC, curses.KEY_F2, ord("\n")]:  # Deactivate box
            self.hover()
        elif key == curses.KEY_DOWN:
            if self._scroll_y < smy:
                self._scroll_y += 1
        elif key == curses.KEY_UP:
            if self._scroll_y > 0:
                self._scroll_y -= 1
        elif key == curses.KEY_LEFT:
            if self._scroll_x > 0:
                self._scroll_x -= 1
        elif key == curses.KEY_RIGHT:
            if self._scroll_x < smx:
                self._scroll_x += 1

    def _capture_take(self, origin: Tuple[int, int], direction: int) -> None:
        """Takeover the capture.
        origin = (y,x), coordinates of the origin cursor"""
        # 0:down, 1: right, 2:up, 3:left
        if self._state == -1 or self._state == 0:
            self.hover()
        elif self._state == 1:
            self.activate()

    def _capture_remove(self, direction: int) -> None:
        """Remove the capture.
        direction 0: down, 1: right, 2: up, 3: left"""
        self._is_drawing_cursor = False
        self.bypass_if_activated = False
        self._state = -1

    def activate(self) -> None:
        """Activate the text input."""
        self._state = 1
        self._is_drawing_cursor = True
        self.bypass_if_activated = True

    def hover(self) -> None:
        """Change text input to hover state."""
        self._state = 0
        self._is_drawing_cursor = False
        self.bypass_if_activated = False

    def deactivate(self) -> None:
        """Deactivate the text input."""
        self._state = -1
        self._is_drawing_cursor = False
        self.bypass_if_activated = False

    def get_hitbox(self) -> Hitbox:
        """Return hitbox of the object."""
        if self._overwritten_hitbox:
            return self._hitbox
        else:
            y, x = self.get_yx()
            return Hitbox((y, x), (y + self._height - 1, x + self._width - 1))
