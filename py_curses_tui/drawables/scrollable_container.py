import curses
import curses.ascii
from math import floor
from typing import List, Optional, Tuple

from ..utility import cwin, try_self_call
from .base_classes import (
    ColorPalette,
    Drawable,
    DrawableContainer,
    GenStr,
    Hitbox,
    KeyCaptureDrawable,
)


# ==== Drawable objects: props ====
class ScrollableContainer(KeyCaptureDrawable):
    """A scrollable area that can contain other drawables.

    This Drawable should be seen as a 'scrollable painting', namely no KeyCaptureDrawable should be added inside.
    """

    # TODO: for now, inherits from KeyCaptureDrawable, perhaps should also inherit from DrawableContainer

    scrollbar_vertical = "┃"
    scrollbar_horizontal = "━"

    def __init__(
        self,
        y: int,
        x: int,
        width: int,
        height: int,
        inside_width: int,
        inside_height: int,
        scroll_multiplier_x: int = 2,
        scroll_multiplier_y: int = 1,
        palette: Optional[ColorPalette] = None,
        parent: Optional[DrawableContainer] = None,
    ):
        """A scrollable area that can contain other drawables.
        This Drawable should be seen as a 'scrollable painting', namely no KeyCaptureDrawable should be added inside.

        Args:
            y (int): y position.
            x (int): x position.
            width (int): width (external).
            height (int): height (external).
            inside_width (int): width of the inside area (internal).
            inside_height (int): height of the inside area (internal).
            scroll_multiplier_x (int, optional): multiplier for the horizontal scroll speed. Defaults to 2.
            scroll_multiplier_y (int, optional): multiplier for the vertical scroll speed. Defaults to 1.
            palette (Optional[ColorPalette], optional): color palette of the object. Defaults to None.
            parent (Optional[DrawableContainer], optional): parent of the object. Defaults to None.

        Color palette:
            box: color of the border.
            box_hover: color of the border when hovered.
            box_selected: color of the border when selected.

        on_update:
            Called when:
                scrollable_container.add() is called.
                scrollable_container.clear() is called.
                scrollable_container.update_pad_size() is called.
            Supressed before first draw.
        """

        if width < 3 or height < 3:
            raise ValueError("Width and height must be at least 3.")
        super().__init__(y, x, parent)
        self._width = width
        self._height = height
        self._inside_width = inside_width  # take borders into account
        self._inside_height = inside_height
        self.scroll_multiplier_x = scroll_multiplier_x
        self.scroll_multiplier_y = scroll_multiplier_y
        self.set_palette(palette, False) # None if not set, should be overwritten when adding to a container

        self._drawables: List[Drawable] = []  # TODO: for now, only drawables, no kcds
        self._scroll_x = 0
        self._scroll_y = 0

        self._pad = curses.newpad(self._inside_height, self._inside_width)
        self._pad.bkgdset(" ", curses.color_pair(self._get_palette_bypass().box))
        self._state = -1  # -1: unfocused, 0: hover, 1: active

        # self.capture_goto: Callable[[Tuple[int, int], int], Any] = None
        self.capture_take = self._capture_take
        self.capture_remove = self._capture_remove

        self._first_draw = False  # whether it was drawn once. Sort of init

    def _capture_take(self, origin: Tuple[int, int], direction: int) -> None:
        self._state = 0

    def _capture_remove(self, direction: int) -> None:
        self._state = -1

    def add(self, obj: Drawable) -> None:
        """Overwrite parent"""
        self._drawables.append(obj)

        if self._first_draw:  # supressed before first draw
            if self.on_update:
                try_self_call(self, self.on_update)

    def clear(self) -> None:
        self._drawables.clear()

        if self._first_draw:  # supressed before first draw
            if self.on_update:
                try_self_call(self, self.on_update)

    def draw(self, window: cwin) -> None:
        if not self._first_draw:
            self._first_draw = True
        y, x = self.get_yx()

        # == Draw the border ==
        if self._state == -1:
            Drawable.rectangle(
                window, (y, x), (y + self._height - 1, x + self._width - 1), self._get_palette_bypass().box
            )
        elif self._state == 0:
            Drawable.rectangle(
                window,
                (y, x),
                (y + self._height - 1, x + self._width - 1),
                self._get_palette_bypass().box_hover,
            )
        elif self._state == 1:
            Drawable.rectangle(
                window,
                (y, x),
                (y + self._height - 1, x + self._width - 1),
                self._get_palette_bypass().box_selected,
            )

        window.noutrefresh()

        # == Draw pad content ==
        self._pad.erase()
        for obj in self._drawables:
            obj.draw(self._pad)
        try:
            self._pad.noutrefresh(
                self._scroll_y,
                self._scroll_x,
                self.y + 1,
                self.x + 1,
                self.y + self._height - 2,
                self.x + self._width - 2,
            )
        except Exception:
            pass
        # == Draw the scrollbars ==
        if self._inside_height > self._height - 2:
            self._draw_vertical_scrollbar(window, y, x)
        if self._inside_width > self._width - 2:
            self._draw_horizontal_scrollbar(window, y, x)

    def _draw_vertical_scrollbar(self, window: cwin, y: int, x: int) -> None:
        scrollbar_height = int(max(1, floor(self._height / self._inside_height * self._height)))
        scrollbar_y_f = (
            (self._height - scrollbar_height)
            / (self._inside_height - self._height + 2)
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

        xf = x + self._width
        for yf in range(y, self._height + y):
            Drawable.draw_str(
                GenStr(
                    " " * len(self.scrollbar_vertical)
                    if (yf < y + scrollbar_y or yf >= y + scrollbar_y + scrollbar_height)
                    else self.scrollbar_vertical
                ),
                window,
                yf,
                xf,
                [],
                self._get_palette_bypass().scrollbar,
            )

    def _draw_horizontal_scrollbar(self, window: cwin, y: int, x: int) -> None:
        scrollbar_width = int(max(1, floor(self._width / self._inside_width * self._width)))
        scrollbar_x_f = (
            (self._width - scrollbar_width)
            / (self._inside_width - self._width + 2)
            * self._scroll_x
        )

        if scrollbar_x_f > 0 and round(scrollbar_x_f) == 0:
            scrollbar_x = 1
        elif (
            scrollbar_x_f < self._width - scrollbar_width
            and round(scrollbar_x_f) == self._width - scrollbar_width
        ):
            scrollbar_x = self._width - scrollbar_width - 1
        else:
            scrollbar_x = round(scrollbar_x_f)

        yf = y + self._height
        for xf in range(x, self._width + x):
            Drawable.draw_str(
                GenStr(
                    " " * len(self.scrollbar_horizontal)
                    if (xf < x + scrollbar_x or xf >= x + scrollbar_x + scrollbar_width)
                    else self.scrollbar_horizontal
                ),
                window,
                yf,
                xf,
                [],
                self._get_palette_bypass().scrollbar,
            )

    def scroll(self, dy: int, dx: int) -> None:
        """Scroll the area by the given amount."""
        dy, dx = dy * self.scroll_multiplier_y, dx * self.scroll_multiplier_x  # apply multiplier
        maxscrolly = self._inside_height - self._height + 2
        maxscrollx = self._inside_width - self._width + 2

        self._scroll_y += dy
        self._scroll_x += dx
        if self._scroll_y < 0:
            self._scroll_y = 0
        elif self._scroll_y > maxscrolly:
            self._scroll_y = maxscrolly
        if self._scroll_x < 0:
            self._scroll_x = 0
        elif self._scroll_x > maxscrollx:
            self._scroll_x = maxscrollx

        # if too tiny, scroll to 0
        if self._inside_height <= self._height - 2:
            self._scroll_y = 0
        if self._inside_width <= self._width - 2:
            self._scroll_x = 0

        # raise ValueError(f"scroll_y: {self._scroll_y}, scroll_x: {self._scroll_x}")

    def scroll_x(self, dx: int) -> None:
        """Scroll the area horizontally by the given amount."""
        self.scroll(0, dx)

    def scroll_y(self, dy: int) -> None:
        """Scroll the area vertically by the given amount."""
        self.scroll(dy, 0)

    def update_pad_size(self, inside_width: int, inside_height: int) -> None:
        """Update the size of the pad. Mainly meant to be used to inscrease the size, as the scrolls are not updated."""
        self._inside_width = inside_width
        self._inside_height = inside_height
        self._pad.resize(self._inside_height, self._inside_width)

        if self._first_draw:  # supressed before first draw
            if self.on_update:
                try_self_call(self, self.on_update)

    def reset_scroll(self):
        """Reset the scroll to origin."""
        self._scroll_x = 0
        self._scroll_y = 0

    def key_behaviour(self, key: int) -> None:
        if self._state == -1 or self._state == 1:  # if active or unfocused
            self._key_behaviour_active(key)
        elif self._state == 0:  # if hover
            self._key_behaviour_hover(key)

        # key behaviour of objects
        for obj in self._drawables:
            obj.key_behaviour(key)

    def _key_behaviour_hover(self, key: int) -> None:
        if key == ord("\n"):
            self._state = 1
        elif key == curses.KEY_DOWN:
            if self.capture_goto:
                self._state = -1
                self.capture_goto((self.y + self._height - 1, self.x), 0)
        elif key == curses.KEY_UP:
            if self.capture_goto:
                self._state = -1
                self.capture_goto((self.y - 1, self.x), 2)
        elif key == curses.KEY_RIGHT:
            if self.capture_goto:
                self._state = -1
                self.capture_goto((self.y, self.x + self._width - 1), 1)
        elif key == curses.KEY_LEFT:
            if self.capture_goto:
                self._state = -1
                self.capture_goto((self.y, self.x - 1), 3)

    def _key_behaviour_active(self, key: int) -> None:
        if key == curses.KEY_DOWN:
            self.scroll_y(1)
        elif key == curses.KEY_UP:
            self.scroll_y(-1)
        elif key == curses.KEY_LEFT:
            self.scroll_x(-1)
        elif key == curses.KEY_RIGHT:
            self.scroll_x(1)
        elif key in [curses.ascii.ESC, ord("\n")]:
            self._state = 0

    def get_hitbox(self) -> Hitbox:
        """Return hitbox of the object."""
        return Hitbox((self.y, self.x), (self.y + self._height - 1, self.x + self._width - 1))

    def overwrite_hitbox(self, hitbox: Hitbox, relative: bool = False) -> None:
        """Overwrite the hitbox of the object."""
        raise NotImplementedError("ScrollableContainer does not support hitbox overwriting.")

    def reset_hitbox(self) -> None:
        """Reset the hitbox of the object."""
        raise NotImplementedError(
            "ScrollableContainer does not support hitbox overwriting, thus reset_hitbox is not defined."
        )

    def set_palette(self, palette, should_override = False) -> None:
        """Set the color palette of the objects."""
        super().set_palette(palette, should_override)
        for obj in self._drawables:
            obj.set_palette(palette, should_override)
    
    def get_palette(self) -> ColorPalette:
        """Return the color palette of the object."""
        return super().get_palette()
    