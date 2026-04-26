"""
Button drawable.
"""

import curses
from ..core import Drawable
from ..genstr import GenStr
from typing import Optional, override
from ..utils.draw_utils import draw_genstr
from ..core import KeyBehaviourFlag

class Button(Drawable):
    """A simple button element."""

    @override
    def __init__(self, text: str, y: int, x: int, width: Optional[int] = None, parent: Drawable | None = None):
        """A simple button element.
        
        If width is set, will try to center the button text within the width. If the text is wider than the width, it will be truncated."""
        super().__init__(y, x, parent)
        self.text = text
        self.width = width
        self._is_selected = False

    @override
    def draw(self, window) -> None:
        """Draw the button element."""
        super().draw(window)
        y, x = self._get_y_x()

        text_to_draw: str = self.text
        if self.width is not None:
            if len(self.text) > self.width:
                text_to_draw = self.text[:self.width]
            else:
                padding_left = (self.width - len(self.text)) // 2
                padding_right = self.width - len(self.text) - padding_left
                text_to_draw = ' ' * padding_left + self.text + ' ' * padding_right

        if self._is_selected:
            window.attron(curses.A_REVERSE)
        draw_genstr(window, y, x, GenStr(text_to_draw) + f" {self._is_selected=}")
        if self._is_selected:
            window.attroff(curses.A_REVERSE)
    
    @override
    def capture(self, y_prev: int, x_prev: int) -> bool:
        """Whether the Drawable can be selected."""
        return True  # Non-capturing drawable.
    
    @override
    def key_behaviour(self, key: int) -> KeyBehaviourFlag:
        # Remove capture
        if key in (curses.KEY_UP, curses.KEY_DOWN, curses.KEY_LEFT, curses.KEY_RIGHT):
            return KeyBehaviourFlag.EXIT

        # Action on Enter
        if key == ord('\n'):
            self._is_selected = not self._is_selected
            return KeyBehaviourFlag.HANDLED

        return KeyBehaviourFlag.SKIPPED