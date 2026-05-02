"""
Choose drawable.
"""

import curses
from typing import Optional, override, Callable

from py_curses_tui.utils.colors import Palette
from ..core import Drawable, KeyBehaviourFlag
from ..genstr import GenStr
from ..utils.draw_utils import draw_genstr
from ..utils.misc import padded_text


class Choose(Drawable):
    """Drawable with multiple choices."""

    @override
    def __init__(
        self,
        y: int,
        x: int,
        options: list[tuple[str, Callable[["Choose"], None]]] = [],
        width: Optional[int] = None,
        parent: Optional[Drawable] = None,
        palette: Optional[Palette] = None,
    ):
        """Drawable with multiple choices, each choice can be selected and trigger an action when Enter is pressed.

        If no width is provided, the choose will be as wide as the longest choice text.

        Palette:
            - secondary: The default color pair for text of choices."""
        super().__init__(y, x, parent, palette)
        self.options = options
        self.selected_index: Optional[int] = None
        self.update_width(
            width
        )  # Set width based on longest option text if not provided.

    def update_width(self, width: Optional[int] = None) -> None:
        """Update the width of the choose based on the longest option text."""
        if width:
            self.width = width
        else:
            self.width = (
                max(len(option[0]) for option in self.options) if self.options else 0
            )

    @override
    def draw(self, window) -> None:
        """Draw the button element."""
        super().draw(window)
        y, x = self._get_y_x()
        palette = self.get_palette()

        for i, (option_text, _) in enumerate(self.options):
            is_selected = (i == self.selected_index)
            attrs: list[int] = [curses.A_STANDOUT] if is_selected else []
            text_to_draw = padded_text(option_text, self.width) if self.width is not None else option_text
            draw_genstr(
                window,
                y + i,  # Draw each option on a new line.
                x,
                GenStr((text_to_draw, None, attrs)),
                palette.secondary,
            )

    @override
    def capture(self, y_prev: int, x_prev: int) -> bool:
        """Whether the Drawable can be selected."""
        if not self.options:
            return False  # No options, cannot be selected.

        y, x = self._get_y_x() # TODO: use hitbox
        if (y_prev < y):
            self.selected_index = 0 # Select the first option when capturing.
        else:
            self.selected_index = len(self.options) - 1 # Select the last option when capturing.
        return True
        

    def _on_exit(self) -> None:
        """Called when the Drawable is deselected."""
        self.selected_index = None

    @override
    def key_behaviour(self, key: int) -> KeyBehaviourFlag:
        if key in (curses.KEY_LEFT, curses.KEY_RIGHT):
            self._on_exit()
            return KeyBehaviourFlag.EXIT
        
        elif key == curses.KEY_UP:
            if self.selected_index is None or self.selected_index == 0:
                self._on_exit()
                return KeyBehaviourFlag.EXIT
            # else: move up
            self.selected_index -= 1
            return KeyBehaviourFlag.HANDLED
        
        elif key == curses.KEY_DOWN:
            if self.selected_index is None or self.selected_index == len(self.options) - 1:
                self._on_exit()
                return KeyBehaviourFlag.EXIT
            # else: move down
            self.selected_index += 1
            return KeyBehaviourFlag.HANDLED
        
        elif key == ord("\n"): # Enter key
            if self.selected_index is not None:
                _, action = self.options[self.selected_index]
                action(self)  # Call the action.
                return KeyBehaviourFlag.HANDLED

        return KeyBehaviourFlag.SKIPPED
