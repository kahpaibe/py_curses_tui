import curses
from typing import Optional, Tuple

from ..utility import cwin, inserted_text, try_self_call
from .base_classes import (
    AttrStr,
    ColorPalette,
    Drawable,
    Hitbox,
    KeyCaptureDrawable,
)


# ==== Drawable objects: props ====
class TextInput(KeyCaptureDrawable):
    """An editable text box. Can be used to input text."""

    def __init__(
        self,
        y: int,
        x: int,
        width: int = 1,
        max_length: int = 0,
        parent: Drawable | None = None,
        palette: Optional[ColorPalette] = ColorPalette(),
    ):
        """An editable text box. Can be used to input text.

        Args:
            y (int): y coordinate
            x (int): x coordinate
            width (int, optional): width of the text box. Defaults to 1.
            max_length (int, optional): maximum length of the text, 0 for no limit. Defaults to 0.
            parent (Drawable, optional): parent in hierarchy (e.g. may be used for relative coordinates).
            palette (ColorPalette, optional): color palette. Defaults to ColorPalette().

        Supported keys:
            - printable characters : write character at cursor position
            - backspace : delete selected character
            - delete : delete next character
            - left arrow : move left
            - right arrow : move right
            - up arror, shift + left arrow (begin) : move to beginning of the box
            - down arrow, shift + right arrow (end) : move to end of the box
            - enter, ESC, F2 or move : quit the text box

        Color palette:
            text_edit_text: color of the text.
            text_edit_inactive: color of the text when inactive.
            text_edit_hover: color of the text when hovered.
            text_edit_cursor: color of the cursor.
            text_edit_full: color of the text when full.

        on_update:
            Called when:
                textinput.set_text() is called.
                textinput.hover() is called. (Finished editing, called when pressing Esc or F2)
            Supressed before first draw.
        """
        super().__init__(y, x, parent)
        self.bypass_if_activated = False  # ignore q press to quit the program, and such inputs
        self._width = width  # maximum width
        self._text: str = ""
        self.palette = palette
        self._current_col = 0  # current column in line
        self._state: int = -1  # state of the text box -1: unfocused, 0: hover, 1: active
        self._is_drawing_cursor: bool = False  # whether the cursor should be drawn

        self._max_length = max_length
        self._scroll_x = 0

        self.capture_take = self._capture_take
        self.capture_remove = self._capture_remove

        self._first_draw = False  # whether it was drawn once. Sort of init
        self._just_captured = False  # If was just captured, to avoid spamming self.on_update

    def set_text(self, text: str) -> None:
        """Set the text in the text box."""
        self._text = text
        if self._max_length > 0 and len(text) > self._max_length:
            raise ValueError(
                f"Text too long for the text input with max_length {self._max_length}:\n{self._text}"
            )

        if self._first_draw:  # supressed before first draw
            if self.on_update:
                try_self_call(self, self.on_update)

    def get_text(self) -> str:
        """Get the text in the text box."""
        return self._text

    def draw(self, window: cwin) -> None:
        if not self._first_draw:
            self._first_draw = True
        y, x = self.get_yx()

        t = self._text[self._scroll_x : self._scroll_x + self._width]
        if self._state == -1:  # unfocused
            dl = Drawable.get_str_fixed_size(t, self._width)
            Drawable.draw_str([AttrStr(dl)], window, y, x, [], self.palette.text_edit_inactive)
        elif self._state == 0:  # hover
            dl = Drawable.get_str_fixed_size(t, self._width)
            Drawable.draw_str([AttrStr(dl)], window, y, x, [], self.palette.text_edit_hover)
        else:  # active
            if self._max_length > 0 and self._is_drawing_cursor:
                dl = Drawable.get_str_fixed_size(t, self._width)
                if len(self._text) < self._max_length:
                    it = inserted_text(
                        Drawable.get_str_fixed_size(t, self._width - 1),
                        " ",
                        self._current_col,
                    )
                    Drawable.draw_str(
                        [AttrStr(it)],
                        window,
                        y,
                        x,
                        [],
                        self.palette.text_edit_text,
                    )
                    # draw the cursor separately (bold)
                    Drawable.draw_str(
                        [AttrStr(" ")],
                        window,
                        y,
                        x + self._current_col,
                        [curses.A_BOLD, curses.A_UNDERLINE],
                        self.palette.text_edit_cursor,
                    )
                elif self._current_col + self._scroll_x < len(
                    self._text
                ):  # if full but inside the line
                    Drawable.draw_str([AttrStr(dl)], window, y, x, [], self.palette.text_edit_text)
                    Drawable.draw_str(
                        [AttrStr(self._text[self._current_col + self._scroll_x])],
                        window,
                        y,
                        x + self._current_col,
                        [curses.A_BOLD, curses.A_UNDERLINE],
                        self.palette.text_edit_cursor,
                    )  # draw current char in bold
                else:  # cursor out of bound
                    Drawable.draw_str(
                        [AttrStr(dl)],
                        window,
                        y,
                        x,
                        [curses.A_UNDERLINE, curses.A_BOLD],
                        self.palette.text_edit_full,
                    )
            elif self._max_length <= 0 and self._is_drawing_cursor:
                it = inserted_text(
                    Drawable.get_str_fixed_size(t, self._width - 1),
                    " ",
                    self._current_col,
                )
                Drawable.draw_str(
                    [AttrStr(it)],
                    window,
                    y,
                    x,
                    [],
                    self.palette.text_edit_text,
                )
                # draw the cursor separately (bold)
                Drawable.draw_str(
                    [AttrStr(" ")],
                    window,
                    y,
                    x + self._current_col,
                    [curses.A_BOLD, curses.A_UNDERLINE],
                    self.palette.text_edit_cursor,
                )

            else:
                dl = Drawable.get_str_fixed_size(t, self._width)
                Drawable.draw_str([AttrStr(dl)], window, y, x, [], self.palette.text_edit_text)

    def key_behaviour(self, key: int) -> None:
        if self._state == -1 or self._state == 1:  # if unfocused, object not as capture
            self._key_behaviour_active(key)
        elif self._state == 0:
            self._key_behaviour_hover(key)

    def _key_behaviour_hover(self, key: int) -> None:
        if key in [ord("\n"), curses.KEY_F2]:  # Activate box
            self.activate()
        elif key == curses.KEY_UP:
            if self.capture_goto:
                self._state = -1
                origin = self.get_yx()
                self.capture_goto(origin, 2)
        elif key == curses.KEY_DOWN:
            if self.capture_goto:
                self._state = -1
                y, x = self.get_yx()
                self.capture_goto((y, x), 0)
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

    def _key_behaviour_active(self, key: int) -> None:  # if max_length <= 0
        j = self._current_col
        sx = self._scroll_x
        w = self._width
        maxl = self._max_length
        if maxl > 0:
            msx = max(0, min(maxl, len(self._text)) - w + 1)
        else:  # self._max_length <= 0:
            msx = max(0, len(self._text) - w + 1)

        if curses.ascii.isprint(key):  # if char # TODO: add filter ?
            if maxl > 0:  # limited length
                if j < w - 1 and len(self._text) < maxl:
                    self._text = inserted_text(self._text, chr(key), j + sx)
                    self._current_col += 1
                elif j == w - 1 and len(self._text) < maxl and sx < msx:
                    self._scroll_x += 1
                    self._text = inserted_text(self._text, chr(key), j + sx)
                elif j == w - 1 and len(self._text) < maxl and sx == msx:
                    self._text = inserted_text(self._text, chr(key), j + sx)
            else:  # unlimited length
                if j < self._width - 1:
                    self._text = inserted_text(self._text, chr(key), j + sx)
                    self._current_col += 1
                elif j == self._width - 1:
                    self._text = inserted_text(self._text, chr(key), j + sx)
                    self._scroll_x += 1
        elif key == curses.KEY_BACKSPACE or key == curses.ascii.BS:
            self._press_backspace()
        elif key == curses.KEY_DC:
            self._press_delete()
        elif key == curses.KEY_LEFT:
            if self._current_col > 0:
                self._current_col -= 1
            elif self._current_col == 0 and self._scroll_x > 0:
                self._scroll_x -= 1
            else:  # if self._current_col == 0
                self.hover()
        elif key == curses.KEY_RIGHT:
            if j + sx < len(self._text) and j < min(len(self._text), self._width - 1):
                self._current_col += 1
            elif (
                j + sx < len(self._text)
                and j == min(len(self._text), self._width - 1)
                and self._scroll_x < msx
            ):
                self._scroll_x += 1
            else:  # and self._current_col == len(...)
                self.hover()
        elif key in [curses.KEY_UP]:
            if self._scroll_x > 0:
                self._scroll_x = 0
                self._current_col = 0
            elif self._scroll_x == 0 and self._current_col > 0:
                self._current_col = 0
            else:  # self._current_col == 0 and self._scroll_x == 0:
                self.hover()
        elif key in [curses.KEY_DOWN]:
            if j + sx < len(self._text):
                self._scroll_x = msx
                self._current_col = min(len(self._text) - self._scroll_x, self._width - 1)
            else:  # self._current_col == min(len(self._text), self._width - 1) and self._scroll_x == max_scroll_x
                self.hover()
        elif key == curses.KEY_SLEFT:  # begin
            self._current_col = 0
            self._scroll_x = 0
        elif key == curses.KEY_SRIGHT:  # end
            self._scroll_x = msx
            self._current_col = min(len(self._text) - self._scroll_x, self._width - 1)
        elif key in [ord("\n"), curses.ascii.ESC, curses.KEY_EXIT, curses.KEY_F2]:
            self.hover()

    def _press_backspace(self) -> None:
        j = self._current_col
        sx = self._scroll_x
        if self._current_col > 0:  # inside a line
            self._text = self._text[: j + sx - 1] + self._text[j + sx :]
            self._current_col -= 1
        elif self._current_col == 0 and self._scroll_x > 0:
            self._text = self._text[: j + sx - 1] + self._text[j + sx :]
            self._scroll_x -= 1

    def _press_delete(self) -> None:
        if self._current_col < len(self._text):
            j, sx = self._current_col, self._scroll_x
            self._text = self._text[: sx + j] + self._text[j + sx + 1 :]

    def _capture_take(self, origin: Tuple[int, int], direction: int) -> None:
        """Takeover the capture.
        origin = (y,x), coordinates of the origin cursor"""
        self._just_captured = True

        self._scroll_x = max(len(self._text) - self._width + 1, 0)
        self._current_col = min(max(len(self._text) - self._scroll_x, 0), self._width - 1)
        if self._state == -1 or self._state == 0:
            self.hover()
        elif self._state == 1:
            self.activate()

    def _capture_remove(self, direction: int) -> None:
        """Remove the capture.
        direction 0: down, 1: right, 2: up, 3: left"""
        self._just_captured = False

        self._is_drawing_cursor = False
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

        if self._first_draw and not self._just_captured:  # supressed before first draw
            if self.on_update:
                try_self_call(self, self.on_update)

        if self._just_captured:
            self._just_captured = False

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
            return Hitbox((y, x), (y, x + self._width - 1))
