"""
Button drawable.
"""

import curses
from typing import Optional, override, Callable

from py_curses_tui.utils.colors import Palette
from ..core import Drawable, SignalCaptureRemove
from ..genstr import GenStr
from ..utils.draw_utils import draw_genstr
from ..utils.misc import centered_text

class Button(Drawable):
    """A simple button element."""

    @override
    def __init__(
        self,
        text: str,
        y: int,
        x: int,
        action: Callable[["Button"], None] = lambda button: None,
        width: Optional[int] = None,
        parent: Optional[Drawable] = None,
        palette: Optional[Palette] = None,
    ):
        """A simple button element.

        If width is set, will try to center the button text within the width. If the text is wider than the width, it will be truncated.

        Palette:
            - secondary: The default color pair for the button text."""
        super().__init__(y, x, parent, palette)
        self.text = text
        self.action = action
        self.width = width
        self._is_selected = False

    @override
    def draw(self, window) -> None:
        """Draw the button element."""
        super().draw(window)
        y, x = self.get_y_x()
        palette = self.get_palette()

        text_to_draw: str = (
            centered_text(self.text, self.width)
            if self.width is not None
            else self.text
        )
        
        attrs: list[int] = []
        if self._is_selected:
            attrs.append(curses.A_STANDOUT)

        draw_genstr(
            window,
            y,
            x,
            GenStr((text_to_draw, None, attrs)),
            palette.secondary,
        )

    @override
    def capture(self, y_prev: int, x_prev: int) -> bool:
        """Whether the Drawable can be selected."""
        self._is_selected = True
        return True  # Non-capturing drawable.
    
    def _on_exit(self) -> None:
        """Called when the Drawable is deselected."""
        self._is_selected = False

    @override
    def key_behaviour(self, key: int) -> bool:
        # Remove capture
        if key in (curses.KEY_UP, curses.KEY_DOWN, curses.KEY_LEFT, curses.KEY_RIGHT):
            self._on_exit()
            raise SignalCaptureRemove(*self.get_y_x()) # Remove capture

        # Action on Enter
        if key == ord("\n"):
            self.action(self) # Call the action.
            return True

        return False
