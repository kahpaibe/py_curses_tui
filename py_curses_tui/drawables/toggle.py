import curses
from typing import List, Optional, Tuple

from ..utility import cwin, try_self_call
from .base_classes import ColorPalette, Drawable, GenStr, Hitbox, KeyCaptureDrawable


# ==== Drawable objects: props ====
class Toggle(KeyCaptureDrawable):
    """A simple toggle button, which can be on or off or can cycle through given states."""

    def __init__(
        self,
        y: int,
        x: int,
        states: List[str] = ["[ ]", "[X]"],
        parent: Drawable | None = None,
        palette: Optional[ColorPalette] = None,
    ):
        """A button that can be pressed to execute given action.

        Args:
            text (str | GenStr): text to display. If GenStr is given, it will be flattened.
            y (int): y coordinate
            x (int): x coordinate
            states (List[str], optional): list of states (appearance). Defaults to ["[ ]", "[X]"].
            parent (Drawable, optional): parent in hierarchy (e.g. may be used for relative coordinates).
            palette (ColorPalette, optional): color palette. Defaults to None.

        Color palette:
            button_selected: color of the box when selected.
            button_unselected: color of the box when unselected.

        on_update:
            Called when:
                toggle.set_state() is called.
                changing state.
            Supressed before first draw.
        """
        if len(states) < 1:
            raise ValueError("At least one state is required.")
        super().__init__(y, x, parent)
        self._state = 0
        self._selected = False
        self._states = states
        self.capture_remove = self._capture_remove
        self.capture_take = self._capture_take
        self.set_palette(palette, False) # None if not set, should be overwritten when adding to a container

        self._first_draw = False  # whether it was drawn once. Sort of init

    def draw(self, window: cwin) -> None:
        if not self._first_draw:
            self._first_draw = True

        y, x = self.get_yx()
        if self._selected:
            Drawable.draw_str(
                GenStr(self._states[self._state]),
                window,
                y,
                x,
                default_pair_id=self._get_palette_bypass().button_selected,
            )
        else:
            Drawable.draw_str(
                GenStr(self._states[self._state]),
                window,
                y,
                x,
                default_pair_id=self._get_palette_bypass().button_unselected,
            )

    def key_behaviour(self, key: int) -> None:
        if key in [ord("\n"), ord(" ")]:
            self._state = (self._state + 1) % len(self._states)  # cycle

            if self.on_update:
                try_self_call(self, self.on_update)
        elif key == curses.KEY_DOWN:
            origin = self.get_yx()
            self.capture_goto(origin, 0)
        elif key == curses.KEY_RIGHT:
            y, x = self.get_yx()
            w = max(len(s) for s in self._states)
            self.capture_goto((y, x + w - 1), 1)
        elif key == curses.KEY_UP:
            origin = self.get_yx()
            self.capture_goto(origin, 2)
        elif key == curses.KEY_LEFT:
            origin = self.get_yx()
            self.capture_goto(origin, 3)

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
            if len(self._states) == 0:
                return Hitbox((y, x), (y, x))
            else:
                w = max(len(s) for s in self._states)
                return Hitbox((y, x), (y, x + w - 1))

    def get_state_index(self) -> int:
        """Return current state index."""
        return self._state
    
    def get_state(self) -> str:
        """Return current state."""
        return self._states[self._state]

    def set_state_index(self, state: int) -> None:
        """Set current state index."""
        if state < 0 or state >= len(self._states):
            raise ValueError("State index out of range.")
        self._state = state

        if self._first_draw:  # supressed before first draw
            if self.on_update:
                try_self_call(self, self.on_update)
