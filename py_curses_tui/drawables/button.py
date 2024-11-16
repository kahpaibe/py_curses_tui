import curses
from typing import Any, Callable, Optional, Self, Tuple

from ..utility import cwin, try_self_call
from .base_classes import (
    ColorPalette,
    Drawable,
    GenStr,
    Hitbox,
    KeyCaptureDrawable,
)


# ==== Drawable objects: props ====
class Button(KeyCaptureDrawable):
    """A button that can be pressed to execute given action."""

    def __init__(
        self,
        text: str | GenStr,
        y: int,
        x: int,
        action: Callable[[Self], Any],
        parent: Drawable | None = None,
        palette: Optional[ColorPalette] = ColorPalette(),
        width: int = 0,
        centered: bool = True,
    ):
        """A button that can be pressed to execute given action.

        Args:
            text (str | GenStr): text to display. If GenStr is given, it will be flattened.
            y (int): y coordinate
            x (int): x coordinate
            action (Callable): action to execute.
            parent (Drawable, optional): parent in hierarchy (e.g. may be used for relative coordinates).
            palette (ColorPalette, optional): color palette. Defaults to ColorPalette().
            width (int, optional): width of the button. Defaults to 0. Used for centering.
            centered (bool, optional): whether the text should be centered. Defaults to True. If true, width should be given.

        Color palette:
            button_selected: color of the button when selected.
            button_unselected: color of the button when unselected.

        On update:
            Called when button.set_text() is called.
        Suppressed before first draw.

        The Choice.action action may be provided with a self argument.
        Example:
            choice1.action = lambda selfo: print(selfo.choices) # where selfo is the Button object
        """
        super().__init__(y, x, parent)
        self._selected = False
        self.capture_remove = self._capture_remove
        self.capture_take = self._capture_take
        self.palette = palette

        if isinstance(text, str):
            self._width = width if width > 0 else len(text)
        else:
            self._width = width if width > 0 else len(text[0].text)

        self.action = action
        self.centered = centered
        self._text: GenStr = []
        self._first_draw = False  # Whether it was drawn once. Sort of init
        self.set_text(text)

    def draw(self, window: cwin) -> None:
        if not self._first_draw:
            self._first_draw = True
        y, x = self.get_yx()
        if self._selected:
            Drawable.draw_str(
                self._text,
                window,
                y,
                x,
                default_pair_id=self.palette.button_selected,
                attributes=[curses.A_BOLD],
            )
        else:
            Drawable.draw_str(
                self._text,
                window,
                y,
                x,
                default_pair_id=self.palette.button_unselected,
            )

    def key_behaviour(self, key: int) -> None:
        if key == ord("\n"):
            if self.action:
                try_self_call(self, self.action)
        if key == curses.KEY_UP:
            if self.capture_goto:
                origin = self.get_hitbox().tl
                self.capture_goto(origin, 2)  # goto up
        elif key == curses.KEY_DOWN:
            if self.capture_goto:
                origin = self.get_hitbox().tl
                self.capture_goto(origin, 0)  # goto down
        elif key == curses.KEY_LEFT:
            if self.capture_goto:
                origin = self.get_hitbox().tl
                self.capture_goto(origin, 3)  # goto left
        elif key == curses.KEY_RIGHT:
            if self.capture_goto:
                origin = self.get_hitbox().br
                self.capture_goto(origin, 1)  # goto right

    def _capture_take(self, origin: Tuple[int, int], direction: int) -> None:
        """Takeover the capture.
        origin = (y,x), coordinates of the origin cursor"""
        self._selected = True

    def _capture_remove(self, direction: int) -> None:
        """Remove the capture.
        direction 0: down, 1: right, 2: up, 3: left"""
        self._selected = False

    def get_hitbox(self) -> Hitbox:
        """Return hitbox of the object."""
        if self._overwritten_hitbox:
            return self._hitbox
        else:
            y, x = self.get_yx()
            w = len(self._text)
            return Hitbox((y, x), (y, x + w - 1))

    def get_text(self) -> str:
        """Return text of the button."""
        return self._text[0].text

    def set_text(self, str_or_genstr: str | GenStr) -> None:
        """Set text of the button.

        Args:
            str_or_genstr (str | GenStr): text to set. Can be a simple string or a GenStr.

        If GenStr is given, it will be flattened.

        Calls self.on_update if it exists."""
        # TODO: for now, no GenStr formatting is supported
        if isinstance(str_or_genstr, str):
            t = Drawable.get_str_fixed_size(str_or_genstr, self._width, self.centered)
            self._text = GenStr(t)
        else:
            try:
                t = " ".join(s.text for s in str_or_genstr)
            except AttributeError:
                raise AttributeError(
                    f"GenStr expected, got {str_or_genstr = } of type {type(str_or_genstr)}"
                )
            self._text = GenStr(Drawable.get_str_fixed_size(t, self._width, self.centered))

        if self._first_draw:  # supressed before first draw
            if self.on_update:
                try_self_call(self, self.on_update)
