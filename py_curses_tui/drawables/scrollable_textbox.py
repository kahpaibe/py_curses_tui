import curses
from math import floor
from typing import Optional, Tuple

from ..utility import cwin, inserted_text, try_self_call
from .base_classes import (
    ColorPalette,
    Drawable,
    GenStr,
    Hitbox,
    KeyCaptureDrawable,
)


# ==== Drawable objects: props ====
class ScrollableTextBox(KeyCaptureDrawable):
    """A text box that can be scrolled through and edited."""

    arrow_up = "^ "  # up arrow symbol
    arrow_down = "v "  # down arrow symbol
    scrollbar_v = "┃"  # vertical scrollbar symbol
    # scrollbar_h = "━"  # horizontal scrollbar symbol # TODO: add horizontal bar ?

    def __init__(
        self,
        y: int,
        x: int,
        height: int,
        width: int,
        text: str = "",
        scroll_type: int = 0,
        fill_background: bool = True,
        palette: Optional[ColorPalette] = None,
        parent: Drawable | None = None,
    ):
        """An item box that can be scrolled through and edited.
        Warning: it is a complex objects, bugs are likely to appear (hopefully not).

        Args:
            y (int): y coordinate
            x (int): x coordinate
            height (int, optional): height of the text box. Defaults to 1.
            width (int, optional): width of the text box. Defaults to 1.
            text (str, optional): text the object contains when creating the object. Defaults to ""
            scroll_type (int, optional default=0) 0: no scroll bar, 1: basic scroll bar, 2: arrows
            fill_background (bool, optional): whether the background should be filled. Defaults to True.
            palette (ColorPalette, optional): color palette. Defaults to None.
            parent (Drawable, optional): parent in hierarchy (e.g. may be used for relative coordinates).

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
            - ESC : quit the text box

        Color palette:
            text_edit_text: color of the text.
            text_edit_inactive: color of the text when inactive.
            text_edit_hover: color of the text when hovered.
            text_edit_cursor: color of the cursor.
            text_edit_full: color of the text when cursor is out of bound.
            scrollbar: color of the arrows or scrollbar.

        on_update:
            Called when:
                scrollable_textbox.set_text() is called.
                scrollable_textbox.clear_text() is called.
                scrollable_textbox.hover() is called. (Finished editing, called when pressing Esc or F2)
            Supressed before first draw."""

        super().__init__(y, x, parent)
        self._height, self._width = height, width  # maximum width and height
        self._texts = ""
        self._first_draw = False  # whether it was drawn once. Sort of init
        self._just_captured = False  # If was just captured, to avoid spamming self.on_update

        self.set_text(text)
        self._scroll_type = scroll_type
        self.set_palette(palette, False) # None if not set, should be overwritten when adding to a container

        self.capture_take = self._capture_take
        self.capture_remove = self._capture_remove

        self._scroll_y = 0  # vertical scroll position
        self._scroll_x = 0  # horizontal scroll position
        self._current_line = 0  # current line
        self._current_col = 0  # current column in line

        self._state: int = -1  # state of the text box -1: unfocused, 0: hover, 1: active
        self._is_drawing_cursor: bool = False  # whether the cursor should be drawn
        self.fill_background = fill_background
        self.bypass_if_activated = False  # ignore q press to quit the program, and such inputs

    def set_text(self, text: str) -> None:
        """Set the text in the text box."""
        self._texts = text.split("\n")

        if self._first_draw:  # supressed before first draw
            if self.on_update:
                try_self_call(self, self.on_update)

    def clear_text(self) -> None:
        """Clear all text of the TextBox"""
        self.set_text("")

        if self._first_draw:  # supressed before first draw
            if self.on_update:
                try_self_call(self, self.on_update)

    def get_text(self) -> str:
        """Get the text in the text box."""
        return "\n".join(self._texts)

    def draw(self, window: cwin) -> None:
        if not self._first_draw:
            self._first_draw = True
        y, x = self.get_yx()
        sx = self._scroll_x  # sy =  self._scroll_y
        # j = self._current_col
        if len(self._texts) > 0:
            xf = x + len(self.arrow_up)
            if self._state == -1:  # unfocused
                if self.fill_background:
                    for i in range(len(self._texts), self._height):
                        gs = GenStr(" " * self._width)
                        Drawable.draw_str(
                            gs, window, y + i, xf, [], self._get_palette_bypass().text_edit_inactive
                        )
                for i in range(0, min(self._height, len(self._texts))):
                    line = self._texts[i + self._scroll_y]
                    yf = y + i
                    dl = Drawable.get_str_fixed_size(line[sx:], self._width)
                    gs = GenStr(dl)
                    Drawable.draw_str(gs, window, yf, xf, [], self._get_palette_bypass().text_edit_inactive)
            elif self._state == 0:  # hover
                if self.fill_background:
                    for i in range(len(self._texts), self._height):
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
                if not self._is_drawing_cursor:
                    if self.fill_background:
                        for i in range(len(self._texts), self._height):
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
                else:  # active and drawing cursor
                    for i in range(0, min(self._height, len(self._texts))):
                        line = self._texts[i + self._scroll_y]
                        yf = y + i
                        if i + self._scroll_y == self._current_line:
                            gs = GenStr(
                                inserted_text(
                                    Drawable.get_str_fixed_size(line[sx:], self._width - 1),
                                    " ",
                                    self._current_col,
                                )
                            )
                            Drawable.draw_str(
                                gs,
                                window,
                                yf,
                                xf,
                                [],
                                self._get_palette_bypass().text_edit_text,
                            )
                            # draw the cursor separately (bold)
                            Drawable.draw_str(
                                GenStr(" "),
                                window,
                                yf,
                                xf + self._current_col,
                                [curses.A_UNDERLINE, curses.A_BOLD],
                                self._get_palette_bypass().text_edit_text,
                            )
                        else:
                            dl = Drawable.get_str_fixed_size(line[sx:], self._width)
                            Drawable.draw_str(
                                GenStr(dl), window, yf, xf, [], self._get_palette_bypass().text_edit_text
                            )
                    if self.fill_background:
                        for i in range(len(self._texts), self._height):
                            Drawable.draw_str(
                                GenStr(" " * self._width),
                                window,
                                y + i,
                                xf,
                                [],
                                self._get_palette_bypass().text_edit_text,
                            )
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
        i, j = self._current_line, self._current_col
        if curses.ascii.isprint(key):  # if  # TODO: add filter ?
            self._texts[i] = inserted_text(self._texts[i], chr(key), j + self._scroll_x)
            if j < self._width - 1:
                self._current_col += 1
            else:
                self._scroll_x += 1
        elif key == curses.KEY_BACKSPACE or key == curses.ascii.BS:
            self._press_backspace()
        elif key == curses.KEY_DC:
            self._press_delete()
        elif key == ord("\n"):
            self._press_newline()
        elif key in [curses.ascii.ESC, curses.KEY_F2]:
            self.hover()
        else:
            self._key_behaviour_active_navigation(key)

    def _press_backspace(self) -> None:
        j, sy, sx = self._current_col, self._scroll_y, self._scroll_x
        i = self._current_line - self._scroll_y  # y position of selected line. Should be >= 0
        cl = self._current_line
        smy = max(len(self._texts) - self._height, 0)
        if j > 0:  # inside a line
            self._texts[cl] = self._texts[cl][: j + sx - 1] + self._texts[cl][j + sx :]
            if sx + self._width > len(self._texts[i]) + 1 and sx > 0:
                self._scroll_x -= 1
            else:
                self._current_col -= 1
        elif i > 0 and sy < smy:  # and j==0
            self._scroll_x = max(len(self._texts[self._current_line - 1]) - self._width + 1, 0)
            self._current_col = min(
                max(len(self._texts[self._current_line - 1]) - sx, 0), self._width - 1
            )
            self._texts[self._current_line - 1] += self._texts[self._current_line]
            self._texts.pop(self._current_line)
            self._current_line -= 1
        elif i > 0 and sy == smy:  # nd cc==0
            self._current_col = len(self._texts[self._current_line - 1])
            self._texts[self._current_line - 1] += self._texts[self._current_line]
            self._texts.pop(self._current_line)

            self._scroll_x = max(len(self._texts[self._current_line - 1]) - self._width + 1, 0)
            self._current_col = min(
                max(len(self._texts[self._current_line - 1]) - sx, 0), self._width - 1
            )
            self._current_line -= 1
            self._scroll_y -= 1
        elif cl > 0:  # yc == 0 and self.scroll > 0
            self._current_col = len(self._texts[self._current_line - 1])
            self._texts[self._current_line - 1] += self._texts[self._current_line]
            self._texts.pop(self._current_line)

            self._scroll_x = max(len(self._texts[self._current_line - 1]) - self._width + 1, 0)
            self._current_col = min(
                max(len(self._texts[self._current_line - 1]) - sx, 0), self._width - 1
            )
            self._scroll_y = self._scroll_y - 1
            self._current_line -= 1
        else:  # cl==0, s==0, yc==0
            pass
        # do after
        if len(self._texts) < self._height:  # additionnal case if too small
            self._scroll_y = 0

    def _press_delete(self) -> None:
        i, j = self._current_line - self._scroll_y, self._current_col
        texts = self._texts
        sx = self._scroll_x  # sy = self._scroll_y

        if (
            len(texts) > 1
            and j + sx == 0
            and len(texts[i]) == 0
            and self._current_line < len(texts) - 1
        ):
            self._texts.pop(i)
            if len(texts) <= self._height:  # if too small
                self._scroll_y = 0
        elif len(texts) > 1 and j + sx == len(texts[i]) and self._current_line < len(texts) - 1:
            self._texts[i] += self._texts[i + 1]
            self._texts.pop(i + 1)
        elif j + sx < len(texts[i]):
            self._texts[i] = self._texts[i][: j + sx] + self._texts[i][j + sx + 1 :]

    def _press_newline(self) -> None:
        i = self._current_line - self._scroll_y  # y position of selected line. Should be >= 0
        sx = self._scroll_x

        line = self._texts[self._current_line]
        self._texts[self._current_line] = line[: self._current_col + sx]
        self._texts.insert(self._current_line + 1, line[self._current_col + sx :])
        self._current_line = self._current_line + 1
        self._current_col = 0
        self._scroll_x = 0

        if i == self._height - 1:
            self._scroll_y += 1

    def _key_behaviour_active_navigation(self, key: int) -> None:
        i, j = self._current_line - self._scroll_y, self._current_col
        sx, sy = self._scroll_x, self._scroll_y
        if key in [curses.KEY_EXIT, curses.ascii.ESC]:  # Disable
            self.hover()
        elif key in [curses.KEY_UP]:
            if self._current_line > 0:  # not at the topmost line
                cl = self._current_line
                self._current_line -= 1
                self._scroll_x = min(sx, max(len(self._texts[cl - 1]) - self._width + 1, 0))
                self._current_col = min(j + sx, max(0, len(self._texts[cl - 1]) - self._scroll_x))
                if i == 0 and self._scroll_y > 0:
                    self._scroll_y -= 1
            elif self._scroll_y == 0:  # and self._current_line == 0  # at the top
                if j + sx > 0:
                    self._current_col = 0
                    self._scroll_x = 0
                else:  # exit
                    self.hover()
        elif key in [curses.KEY_DOWN]:
            smy = max(len(self._texts) - self._height, 0)
            if self._current_line < len(self._texts) - 1:  # not at bottom
                self._current_line += 1
                cl = self._current_line
                self._scroll_x = min(sx, max(len(self._texts[cl]) - self._width + 1, 0))
                self._current_col = min(j + sx, max(0, len(self._texts[cl]) - self._scroll_x))
                if i == self._height - 1 and self._scroll_y < smy:
                    self._scroll_y += 1
            elif self._current_line == len(self._texts) - 1:  # bot
                if j + sx < len(self._texts[self._current_line]):
                    self._scroll_x = max(len(self._texts[self._current_line]) - self._width + 1, 0)
                    self._current_col = max(
                        0, len(self._texts[self._current_line]) - self._scroll_x
                    )

                else:  # exit
                    self.hover()
        elif key == curses.KEY_LEFT:
            if j > 0:  # inside a line
                self._current_col -= 1
            elif sx > 0:  # and j == 0
                self._scroll_x -= 1
            elif i == 0 and sy > 0:  # and j == 0 and sx == 0
                self._scroll_y -= 1
                self._current_line -= 1
                self._scroll_x = max(len(self._texts[self._current_line]) - self._width + 1, 0)
                self._current_col = min(
                    max(len(self._texts[self._current_line]) - sx, 0), self._width - 1
                )
            elif i > 0:  # and j == 0 and sx == 0
                self._current_line -= 1
                self._scroll_x = max(len(self._texts[self._current_line]) - self._width + 1, 0)
                self._current_col = min(
                    max(len(self._texts[self._current_line]) - sx, 0), self._width - 1
                )
            elif i == 0 and self._scroll_y == 0:  # and cl==0 and cc==0
                self.hover()
        elif key == curses.KEY_RIGHT:
            smy = max(len(self._texts) - self._height, 0)
            if j + sx < len(self._texts[self._current_line]):  # inside a line
                if j < self._width - 1:
                    self._current_col += 1
                else:
                    self._scroll_x += 1
            elif i < min(self._height - 1, len(self._texts) - 1):
                self._current_line += 1
                self._current_col = 0
                self._scroll_x = 0
            elif self._scroll_y < smy:  # and i < min(self._height - 1, len(self._texts) - 1)
                self._scroll_y += 1
                self._current_line += 1
                self._current_col = 0
                self._scroll_x = 0
            elif self._scroll_y == smy:
                self.hover()
        elif key == curses.KEY_SLEFT:  # begin
            self._current_col, self._current_line = 0, 0
            self._scroll_y = 0
            self._scroll_x = 0
        elif key == curses.KEY_SRIGHT:  # end
            self._current_line = len(self._texts) - 1
            self._scroll_y = max(len(self._texts) - self._height, 0)

            self._scroll_x = max(len(self._texts[self._current_line]) - self._width + 1, 0)
            self._current_col = max(len(self._texts[self._current_line]) - self._scroll_x, 0)

    def _capture_take(self, origin: Tuple[int, int], direction: int) -> None:
        """Takeover the capture.
        origin = (y,x), coordinates of the origin cursor"""
        # 0:down, 1: right, 2:up, 3:left
        self._just_captured = True

        if self._state == -1 or self._state == 0:
            self.hover()
        elif self._state == 1:
            self.activate()

    def _capture_remove(self, direction: int) -> None:
        """Remove the capture.
        direction 0: down, 1: right, 2: up, 3: left"""
        self._just_captured = False

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

        if self._first_draw and not self._just_captured:  # supressed before first draw
            if self.on_update:  # when finished editing
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
            return Hitbox((y, x), (y + self._height - 1, x + self._width - 1))
