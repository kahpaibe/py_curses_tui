import curses
from typing import Iterable, List, Optional, Tuple

from ..utility import cwin, inserted_text, try_self_call
from .base_classes import (
    AttrStr,
    ColorPalette,
    Drawable,
    Hitbox,
    KeyCaptureDrawable,
)


# ==== Drawable objects: props ====
class TextBox(KeyCaptureDrawable):
    """An editable text box. Can be used to input text."""

    def __init__(
        self,
        y: int,
        x: int,
        width: int = 1,
        height: int = 1,
        line_length_bounded: bool = False,
        parent: Drawable | None = None,
        palette: Optional[ColorPalette] = None,
    ):
        """An editable text box. Can be used to input text.

        Args:
            y (int): y coordinate
            x (int): x coordinate
            width (int, optional): width of the text box. Defaults to 1.
            height (int, optional): height of the text box. Defaults to 1.
            line_length_bounded (bool, optional): whether the lines are bounded by the width. Defaults to False.
            parent (Drawable, optional): parent in hierarchy (e.g. may be used for relative coordinates).
            palette (ColorPalette, optional): color palette. Defaults to None.

        Supported keys:
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
            - ESC, F2 or move : quit the text box

        Color palette:
            text_edit_text: color of the text.
            text_edit_inactive: color of the text when inactive.
            text_edit_hover: color of the text when hovered.
            text_edit_cursor: color of the cursor.
            text_edit_full: color of the text when full.

        on_update:
            Called when:
                textbox.set_text() is called.
                textbox.hover() is called. (Finished editing, called when pressing Esc or F2)
            Supressed before first draw.
        """
        super().__init__(y, x, parent)
        self.bypass_if_activated = False  # ignore q press to quit the program, and such inputs
        self._width = width  # maximum width
        self._height = height  # maximum height
        self._texts: List[str] = [""] * height  # list of lines
        self.set_palette(palette, False) # None if not set, should be overwritten when adding to a container
        self._current_line = 0  # current line
        self._current_col = 0  # current column in line
        self._state: int = -1  # state of the text box -1: unfocused, 0: hover, 1: active
        self._is_drawing_cursor: bool = False  # whether the cursor should be drawn

        self._bounded = line_length_bounded  # whether the lines are bounded by the width
        self._scroll_x = 0  # horizontal scroll

        self.capture_take = self._capture_take
        self.capture_remove = self._capture_remove

        self._first_draw = False  # whether it was drawn once. Sort of init
        self._just_captured = False  # If was just captured, to avoid spamming self.on_update

    def set_text(self, text: str | Iterable) -> None:
        """Set the text in the text box."""
        if isinstance(text, str):
            self._texts = text.split("\n")
        elif isinstance(text, Iterable):
            self._texts = list(text)
            while len(self._texts) < self._height:
                self._texts.append("")
        if len(self._texts) > self._height:
            raise ValueError(
                f"Text too long for the text box with height {self._height}:\n{self._texts}"
            )
        if self._bounded:
            if max(len(line) for line in self._texts) > self._width:
                raise ValueError(
                    f"Text too long for the text box with width {self._width}:\n{self._texts}"
                )

        if self._first_draw:  # supressed before first draw
            if self.on_update:
                try_self_call(self, self.on_update)

    def get_text(self) -> str:
        """Get the text in the text box."""
        return "\n".join(self._texts)

    def draw(self, window: cwin) -> None:
        if not self._first_draw:
            self._first_draw = True
        if self._bounded:
            self._draw_bounded(window)
        else:
            self._draw_unbounded(window)

    def _draw_bounded(self, window: cwin) -> None:
        y, x = self.get_yx()

        if self._state == -1:  # unfocused
            for i, line in enumerate(self._texts):
                dl = Drawable.get_str_fixed_size(line, self._width)
                dltext = [AttrStr(dl, None)]
                Drawable.draw_str(dltext, window, y + i, x, [], self._get_palette_bypass().text_edit_inactive)
        elif self._state == 0:  # hover
            for i, line in enumerate(self._texts):
                dl = Drawable.get_str_fixed_size(line, self._width)
                dltext = [AttrStr(dl, None)]
                Drawable.draw_str(dltext, window, y + i, x, [], self._get_palette_bypass().text_edit_hover)
        else:  # active
            if self._is_drawing_cursor:
                for i, line in enumerate(self._texts):
                    dl = Drawable.get_str_fixed_size(line, self._width)
                    if i == self._current_line and len(self._texts[i]) < self._width:
                        t = inserted_text(
                            Drawable.get_str_fixed_size(line, self._width - 1),
                            " ",
                            self._current_col,
                        )
                        Drawable.draw_str(
                            [AttrStr(t, None)],
                            window,
                            y + i,
                            x,
                            [],
                            self._get_palette_bypass().text_edit_text,
                        )
                        # draw the cursor separately (bold)
                        Drawable.draw_str(
                            [AttrStr(" ", None)],
                            window,
                            y + i,
                            x + self._current_col,
                            [curses.A_BOLD, curses.A_UNDERLINE],
                            self._get_palette_bypass().text_edit_cursor,
                        )
                    elif i == self._current_line and self._current_col < len(self._texts[i]):
                        t = [AttrStr(dl, self._get_palette_bypass().text_edit_text)]
                        Drawable.draw_str(t, window, y + i, x, [], self._get_palette_bypass().text_edit_text)
                        Drawable.draw_str(
                            [AttrStr(line[self._current_col], self._get_palette_bypass().text_edit_cursor)],
                            window,
                            y + i,
                            x + self._current_col,
                            [curses.A_BOLD, curses.A_UNDERLINE],
                            self._get_palette_bypass().text_edit_cursor,
                        )  # draw current char in bold
                    elif i == self._current_line:  # cursor out of bound
                        Drawable.draw_str(
                            [AttrStr(dl, None)],
                            window,
                            y + i,
                            x,
                            [curses.A_UNDERLINE, curses.A_BOLD],
                            self._get_palette_bypass().text_edit_full,
                        )
                    else:
                        Drawable.draw_str(
                            [AttrStr(dl)], window, y + i, x, [], self._get_palette_bypass().text_edit_text
                        )
            else:
                for i, line in enumerate(self._texts):
                    dl = Drawable.get_str_fixed_size(line, self._width)
                    Drawable.draw_str(
                        [AttrStr(dl)], window, y + i, x, [], self._get_palette_bypass().text_edit_text
                    )

    def _draw_unbounded(self, window: cwin) -> None:
        y, x = self.get_yx()
        sx = self._scroll_x

        if self._state == -1:  # unfocused
            for i, line in enumerate(self._texts):
                t = line[sx:]
                dl = Drawable.get_str_fixed_size(t, self._width)
                dltext = [AttrStr(dl, None)]
                Drawable.draw_str(dltext, window, y + i, x, [], self._get_palette_bypass().text_edit_inactive)
        elif self._state == 0:  # hover
            for i, line in enumerate(self._texts):
                t = line[sx:]
                dl = Drawable.get_str_fixed_size(t, self._width)
                dltext = [AttrStr(dl, None)]
                Drawable.draw_str(dltext, window, y + i, x, [], self._get_palette_bypass().text_edit_hover)
        else:  # active
            if self._is_drawing_cursor:
                for i, line in enumerate(self._texts):
                    t = line[sx:]
                    dl = Drawable.get_str_fixed_size(t, self._width)
                    # dl = Drawable.get_str_fixed_size(line, self._width)
                    if i == self._current_line:
                        ti = inserted_text(
                            line,
                            " ",
                            self._current_col + sx,
                        )[sx:]
                        tl = Drawable.get_str_fixed_size(ti, self._width)
                        Drawable.draw_str(
                            [AttrStr(tl, None)],
                            window,
                            y + i,
                            x,
                            [],
                            self._get_palette_bypass().text_edit_text,
                        )
                        # draw the cursor separately (bold)
                        Drawable.draw_str(
                            [AttrStr(" ", None)],
                            window,
                            y + i,
                            x + self._current_col,
                            [curses.A_BOLD, curses.A_UNDERLINE],
                            self._get_palette_bypass().text_edit_cursor,
                        )
                    else:
                        Drawable.draw_str(
                            [AttrStr(dl)], window, y + i, x, [], self._get_palette_bypass().text_edit_text
                        )
            else:
                for i, line in enumerate(self._texts):
                    dl = Drawable.get_str_fixed_size(line, self._width)
                    Drawable.draw_str(
                        [AttrStr(dl)], window, y + i, x, [], self._get_palette_bypass().text_edit_text
                    )

    def key_behaviour(self, key: int) -> None:
        if self._state == -1 or self._state == 1:  # if unfocused, object not as capture
            if self._bounded:
                self._key_behaviour_active_bounded(key)
            else:
                self._key_behaviour_active_unbounded(key)
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
                self.capture_goto((y + self._height - 1, x), 0)
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

    def _key_behaviour_active_bounded(self, key: int) -> None:
        i = self._current_line
        j = self._current_col
        if curses.ascii.isprint(key):  # if  # TODO: add filter ?
            if len(self._texts[i]) < self._width:
                self._texts[i] = inserted_text(self._texts[i], chr(key), j)
                self._current_col += 1
        elif key == curses.KEY_BACKSPACE or key == curses.ascii.BS:
            self._press_backspace()
        elif key == curses.KEY_DC:
            self._press_delete()
        elif key == curses.KEY_LEFT:
            if self._current_col > 0:
                self._current_col -= 1
            elif self._current_line > 0:  # and  self._current_col == 0
                self._current_line -= 1
                self._current_col = len(self._texts[self._current_line])
            elif self._current_line == 0:  # and  self._current_col == 0
                self.hover()
        elif key == curses.KEY_RIGHT:
            if self._current_col < len(self._texts[self._current_line]):
                self._current_col += 1
            elif self._current_line < self._height - 1:  # and self._current_col == len(...)
                self._current_line += 1
                self._current_col = 0
            elif i == self._height - 1:  # and self._current_col == len(...)
                self._state = 0  # becomes hover
                self._is_drawing_cursor = False
        elif key in [curses.KEY_UP]:
            if self._current_line > 0:
                self._current_line -= 1
                self._current_col = min(self._current_col, len(self._texts[self._current_line]))
            elif self._current_line == 0 and self._current_col > 0:
                self._current_col = 0
            elif self._current_line == 0 and self._current_col == 0:
                self.hover()
        elif key in [curses.KEY_DOWN]:
            if self._current_line < self._height - 1:
                self._current_line += 1
                self._current_col = min(self._current_col, len(self._texts[self._current_line]))
            elif self._current_line == self._height - 1 and self._current_col < len(self._texts[i]):
                self._current_col = len(self._texts[i])
            elif self._current_line == self._height - 1 and self._current_col == len(
                self._texts[i]
            ):
                self.hover()
        elif key == curses.KEY_SLEFT:  # begin
            self._current_col, self._current_line = 0, 0
        elif key == curses.KEY_SRIGHT:  # end
            self._current_line = self._height - 1
            self._current_col = len(self._texts[self._current_line])
        elif key in [curses.KEY_EXIT, curses.ascii.ESC]:  # Disable
            self.hover()
        elif key == ord("\n"):
            self._press_newline()
        elif key in [curses.ascii.ESC, curses.KEY_F2]:
            self.hover()

    def _key_behaviour_active_unbounded(self, key: int) -> None:
        i = self._current_line
        j = self._current_col
        sx = self._scroll_x
        if curses.ascii.isprint(key):  # if  # TODO: add filter ?*
            self._texts[i] = inserted_text(self._texts[i], chr(key), j + sx)
            if j < self._width - 1:
                self._current_col += 1
            else:
                self._scroll_x += 1
        elif key == curses.KEY_BACKSPACE or key == curses.ascii.BS:
            self._press_backspace()
        elif key == curses.KEY_DC:
            self._press_delete()
        elif key == curses.KEY_LEFT:
            if j > 0:
                self._current_col -= 1
            elif j == 0 and sx > 0:
                self._scroll_x -= 1
            elif i > 0:  # and j == 0 and sx == 0
                self._current_line -= 1
                self._current_col = min(self._width - 1, len(self._texts[self._current_line]))
                self._scroll_x = max(0, len(self._texts[self._current_line]) - self._width + 1)
            elif i == 0:  # and j == 0 and sx == 0
                self.hover()
        elif key == curses.KEY_RIGHT:
            if j < min(self._width - 1, len(self._texts[i]) - sx):
                self._current_col += 1
            elif j + sx < len(self._texts[i]):  # and j == self._width - 1
                self._scroll_x += 1
            elif i < self._height - 1:  # and j == self._width - 1 and sx == len(...)
                self._current_line += 1
                self._current_col = 0
                self._scroll_x = 0
            elif i == self._height - 1:  # and j == self._width - 1 and sx == len(...)
                self.hover()
        elif key in [curses.KEY_UP]:  # TODO: improve
            if i > 0:
                self._current_line -= 1
                self._scroll_x = min(sx, max(len(self._texts[i - 1]) - self._width + 1, 0))
                self._current_col = min(j + sx, max(0, len(self._texts[i - 1]) - self._scroll_x))
            elif i == 0 and j + sx > 0:
                self._current_col = 0
                self._scroll_x = 0
            elif i == 0 and sx == 0:
                self.hover()
        elif key in [curses.KEY_DOWN]:  # TODO: improve
            if i < self._height - 1:
                self._current_line += 1
                self._scroll_x = min(sx, max(len(self._texts[i + 1]) - self._width + 1, 0))
                self._current_col = min(j, max(0, len(self._texts[i + 1]) - self._scroll_x))
            elif i == self._height - 1 and j + sx < len(self._texts[i]):
                self._current_col = self._width - 1
                self._scroll_x = max(0, len(self._texts[i]) - self._width)
            elif i == self._height - 1 and j + sx >= len(self._texts[i]) - 1:
                self.hover()
        elif key == curses.KEY_SLEFT:  # begin
            self._current_col, self._current_line = 0, 0
            self._scroll_x = 0
        elif key == curses.KEY_SRIGHT:  # end
            self._current_line = self._height - 1
            self._current_col = len(self._texts[self._current_line])
            self._scroll_x = max(0, len(self._texts[self._current_line]) - self._width)
        elif key in [curses.KEY_EXIT, curses.ascii.ESC]:  # Disable
            self.hover()
        elif key == ord("\n"):
            self._press_newline()
        elif key in [curses.ascii.ESC, curses.KEY_F2]:
            self.hover()

    def _press_newline(self) -> None:
        if len(self._texts[self._height - 1]) > 0:
            return  # if 'full' do nothing
        if self._current_line == self._height - 1:
            return  # if at the end do nothing
        line = self._texts[self._current_line]
        sx = self._scroll_x
        self._texts[self._current_line] = line[: self._current_col + sx]
        self._texts.insert(self._current_line + 1, line[self._current_col + sx :])
        self._texts.pop(-1)
        self._current_line = self._current_line + 1
        self._current_col = 0
        self._scroll_x = 0

    def _press_backspace(self) -> None:
        if self._bounded:
            if self._current_col > 0:  # inside a line
                self._texts[self._current_line] = (
                    self._texts[self._current_line][: self._current_col - 1]
                    + self._texts[self._current_line][self._current_col :]
                )
                self._current_col -= 1
            elif self._current_line > 0:
                if (
                    len(self._texts[self._current_line - 1]) + len(self._texts[self._current_line])
                    <= self._width
                ):  # if enough space
                    self._current_col = len(self._texts[self._current_line - 1])
                    self._texts[self._current_line - 1] += self._texts[self._current_line]
                    self._texts.pop(self._current_line)
                    self._texts.append("")
                    self._current_line -= 1
                else:  # if not enough space
                    m = self._width - len(self._texts[self._current_line - 1])
                    self._texts[self._current_line - 1] += self._texts[self._current_line][:m]
                    self._texts[self._current_line] = self._texts[self._current_line][m:]
                    self._current_col = len(self._texts[self._current_line - 1])
                    self._current_line -= 1
        else:  # unbounded
            i, j, sx = self._current_line, self._current_col, self._scroll_x
            if j > 0:
                self._texts[i] = self._texts[i][: j + sx - 1] + self._texts[i][j + sx :]
                if sx + self._width > len(self._texts[i]) + 1 and sx > 0:
                    self._scroll_x -= 1
                else:
                    self._current_col -= 1
            elif j == 0 and sx > 0:
                self._texts[i] = self._texts[i][: j + sx - 1] + self._texts[i][j + sx :]
                self._scroll_x -= 1
            elif i > 0:  # and j == 0 and sx == 0 # carry over
                self._scroll_x = max(0, len(self._texts[i - 1]) - self._width + 1)
                self._current_col = min(len(self._texts[i - 1]) - self._scroll_x, self._width - 1)
                self._current_line -= 1
                self._texts[i - 1] += self._texts[i]
                self._texts.pop(i)
                self._texts.append("")

    def _press_delete(self) -> None:
        if self._bounded:
            if self._current_col == 0 and len(self._texts[self._current_line]) == 0:
                self._texts.pop(self._current_line)
                self._texts.append("")
            elif (
                self._current_col == len(self._texts[self._current_line])
                and self._current_line < self._height - 1
            ):
                if (
                    len(self._texts[self._current_line + 1]) + len(self._texts[self._current_line])
                    <= self._width
                ):
                    self._texts[self._current_line] += self._texts[self._current_line + 1]
                    self._texts.pop(self._current_line + 1)
                    self._texts.append("")
                else:  # if not enough space
                    m = self._width - len(self._texts[self._current_line])
                    self._texts[self._current_line] += self._texts[self._current_line + 1][:m]
                    self._texts[self._current_line + 1] = self._texts[self._current_line + 1][m:]

            elif self._current_col < len(self._texts[self._current_line]):
                self._texts[self._current_line] = (
                    self._texts[self._current_line][: self._current_col]
                    + self._texts[self._current_line][self._current_col + 1 :]
                )
        else:  # unbounded
            i, j, sx = self._current_line, self._current_col, self._scroll_x
            if j + sx < len(self._texts[i]):
                self._texts[i] = self._texts[i][: j + sx] + self._texts[i][j + sx + 1 :]
            elif j + sx == len(self._texts[i]) and i < self._height - 1:
                self._texts[i] += self._texts[i + 1]
                self._texts.pop(i + 1)
                self._texts.append("")

    def _capture_take(self, origin: Tuple[int, int], direction: int) -> None:
        """Takeover the capture.
        origin = (y,x), coordinates of the origin cursor"""

        self._just_captured = True

        # in all cases
        self._current_line = 0
        self._current_col = 0
        self._scroll_x = 0
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
                try_self_call(
                    self, self.on_update
                )  # TODO: called when capture taking :c -> "just captured" bool ?

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
            return Hitbox((y, x), (y + self._height - 1, x + self._width - 1))
