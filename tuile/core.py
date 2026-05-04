import curses
from curses import window as cwin
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from typing import Literal, Optional, override
from enum import Enum

from .genstr import GenStr
from .utils.draw_utils import draw_genstr, draw_fill
from .utils.distance import Direction, distance
from .utils.colors import (
    COLOR_PAIRS_BW,
    ColorPairs,
    TerminalColors,
    Palette,
    PALETTE_BW,
)

# =====================================
#  Helper Classes
# =====================================


class Signal(Exception):
    """Signal for above layers."""


class SignalRedraw(Signal):  # TODO: to handle
    """Exception to signal a redraw of the UI."""


class SignalExit(Signal):
    """Exception to signal exit of the application."""


class SignalCaptureRemove(Signal):
    """Exception to signal removal of a drawable from capture."""

    def __init__(self, y_from: int, x_from: int, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.y_from = y_from  # y value of removal origin
        self.x_from = x_from  # x value of removal origin


# =====================================
#  Drawable
# =====================================


class Drawable:
    """A drawable object."""

    def __init__(
        self,
        y: int,
        x: int,
        parent: Optional["Drawable"] = None,
        palette: Optional[Palette] = None,
    ):
        """A drawable object.

        Args:
            y (int): y-coordinate of the Drawable object.
            x (int): x-coordinate of the Drawable object.
            parent (Optional[Drawable]): Parent Drawable object for relative coordinates, such as a Menu or another Drawable. If None, the coordinates are absolute to the window.
            palette (Optional[Palette]): Color palette to use for the Drawable. If None, the parent's palette is used.
        """
        self.y, self.x = y, x
        self.parent = parent
        self._first_draw = True  # Whether the drawable has been drawn at least once, used to trigger first draw behaviour.
        self.palette = palette

    def get_y_x(self) -> tuple[int, int]:
        """Get the absolute y and x coordinates of the drawable object, taking into account the parent drawables."""
        if self.parent is None:
            return (self.y, self.x)
        parent_y, parent_x = self.parent.get_y_x()
        return (self.y + parent_y, self.x + parent_x)

    @abstractmethod
    def draw(self, window: cwin) -> None:
        """Draw the object.

        Args:
            window (curses.window): Window to draw on.
        """
        if self._first_draw:
            self._on_first_draw()

    def capture(self, y_prev: int, x_prev: int) -> bool:
        """Whether the Drawable can be selected.

        Args:
            y_prev (int): y-value of the previously selected Drawable.
            x_prev (int): x-value of the previously selected Drawable.

        Return (bool):
            Whether the Drawable can be captured.
        """
        return False  # Non-capturing drawable.

    def key_behaviour(self, key: int) -> bool:
        """Behaviour of the Drawable in reponse to a key input.

        Args:
            - key (int): key to process

        Return (bool):
            True if the key was handled, False if skipped.
        Raises:
            (Signal): Signals to be handled by upper layers, such as the menu or application.
        """
        # Non-capturing drawables by default.
        raise NotImplementedError(
            "Non-capturing Drawable should never receive key input."
        )

    def get_palette(self) -> Palette:
        """Return the color palette for the drawable."""
        if self.palette is not None:
            return self.palette
        elif self.parent is not None:
            return self.parent.get_palette()
        else:
            return PALETTE_BW  # Default palette if no parent and no palette specified.

    def _on_first_draw(self) -> None:
        """Behaviour to execute on the first draw of the drawable object."""
        if self._first_draw:
            self._first_draw = False


# =====================================
#  Submenu
# =====================================


class Submenu(Drawable):
    """Elementary unit for drawable navigation, draws and control drawables it contains."""

    @override
    def __init__(
        self,
        palette: Optional[Palette] = None,
        default_selected: int | Literal["First", "Last"] = "First",
    ):
        """A submenu spanning all the window."""
        super().__init__(0, 0, parent=None, palette=palette)
        self.drawables: list[Drawable] = []
        self._selected_drawable_index: int | None = None
        self._default_selected: int | Literal["First", "Last"] = default_selected

    def select_drawable(self, index: Optional[int]) -> None:
        """Select a drawable by index. This is the expected way to define the selected drawable on application start."""
        self._selected_drawable_index = index
        self._check_selected_drawable()

    def get_selected_drawable_index(self) -> int | None:
        """Get the index of the currently selected drawable.

        Return (int | None):
            Index of the currently selected drawable, or None if no drawable is selected.
        """
        self._check_selected_drawable()
        return self._selected_drawable_index

    @override
    def _on_first_draw(self) -> None:
        if self._default_selected == "First":
            self._capture_best_drawable(0, 0, Direction.DOWN)
        elif self._default_selected == "Last":
            self._capture_best_drawable(curses.LINES, curses.COLS, Direction.UP)
        else:  # int
            self.select_drawable(self._default_selected)

        return super()._on_first_draw()

    @override
    def draw(self, window: cwin) -> None:
        """Draw the menu and its drawables."""
        if self._first_draw:
            self._on_first_draw()

        for drawable in self.drawables:
            drawable.draw(window)

    def _capture_best_drawable(
        self, y_prev: int, x_prev: int, direction: Direction
    ) -> bool:
        """Try capturing the best drawable according to distance."""

        distances: list[tuple[int, int]] = []
        for i, drawable in enumerate(self.drawables):
            d = distance(
                y_prev,
                x_prev,
                *drawable.get_y_x(),
                direction,
                curses.LINES,
                curses.COLS,
            )
            distances.append((d, i))

        distances.sort(key=lambda x: x[0])  # Sort by distance

        # Try capturing the drawables in order of distance until one is captured.
        for _, i in distances:
            if self.drawables[i].capture(y_prev, x_prev):
                self.select_drawable(i)
                return True

        return False

    @override
    def capture(self, y_prev: int, x_prev: int) -> bool:
        """Whether the Drawable can be selected."""
        y, x = self.get_y_x()
        if not self.drawables:  # If no drawable, cannot be captured.
            return False

        # Capture the last drawable if coming from the right or below.
        if x_prev > x or (x_prev == x and y_prev > y):
            if not self._capture_best_drawable(y_prev, x_prev, Direction.DOWN):
                return False  # Coult not capture
        else:  # Capture the first drawable if coming from the left or above, or if there are no drawables.
            if not self._capture_best_drawable(y_prev, x_prev, Direction.UP):
                return False
        return True  # Accept capture.

    @override
    def key_behaviour(self, key: int) -> bool:
        """Behaviour of the Submenu in reponse to a key input.

        Args:
            - key (int): key to process

        Return (bool):
            True if the key was handled, False if skipped.
        Raises:
            (Signal): Signals to be handled by upper layers, such as the menu or application.
        """
        if not self.drawables or self._selected_drawable_index is None:
            return False  # Nothing to do since there is no drawable.

        # Check selected drawable validity.
        self._check_selected_drawable()
        selected_drawable = self.drawables[self._selected_drawable_index]

        # Call selected drawable's key_behaviour
        try:
            flag = selected_drawable.key_behaviour(key)
        except Signal as signal:
            if isinstance(signal, SignalCaptureRemove):  # Capture removal
                # Find next capturing drawable.
                direction = {  # direction flag map
                    curses.KEY_DOWN: Direction.DOWN,
                    curses.KEY_UP: Direction.UP,
                    curses.KEY_LEFT: Direction.LEFT,
                    curses.KEY_RIGHT: Direction.RIGHT,
                }.get(key, None)

                captured = False
                if direction:
                    captured = self._capture_best_drawable(
                        signal.y_from, signal.x_from, direction
                    )
                # If no drawable was captured, try recapturing self from the signal's origin.
                if not captured:
                    return self.capture(signal.y_from, signal.x_from)
                return True

            # Pass signal to upper layers
            raise signal

        return flag

    # @override
    # def _on_first_draw(self) -> None:
    #     super()._on_first_draw()

    def add_drawable(self, drawable: Drawable) -> int:
        """Add a drawable to the menu.

        Args:
            drawable (Drawable): Drawable to add.

        Return (int):
            Index of the added drawable in self.drawables."""
        self.drawables.append(drawable)
        return len(self.drawables) - 1

    def _check_selected_drawable(self) -> None:
        """Check whether the selected drawable index is valid."""
        if self._selected_drawable_index is None:
            return  # No drawable selected, nothing to check.

        if self._selected_drawable_index < 0 or self._selected_drawable_index >= len(
            self.drawables
        ):
            raise ValueError("Selected drawable index out of range.")


# =====================================
#  Menu
# =====================================


class MenuBase(Submenu, ABC):
    """Base class for menus."""

    @override
    def key_behaviour(self, key: int) -> bool:
        # Is itself the main submenu, so exit should be handled carefully
        try:
            flag = super().key_behaviour(key)
        except Signal as signal:
            if isinstance(signal, SignalCaptureRemove):
                if not self.capture(signal.y_from, signal.x_from):
                    raise ValueError(
                        "Main menu should always be able to recapture itself on drawable capture removal."
                    )
            raise signal
        
        return flag


class Menu(MenuBase):
    """A submenu spanning all the window."""

    def __init__(
        self,
        palette: Optional[Palette] = None,
        default_selected: int | Literal["First", "Last"] = "First",
    ):
        """A menu spanning all the window.

        Palette:
            - primary: background color (background of the pair)"""
        super().__init__(palette, default_selected)

    @override
    def draw(self, window: cwin) -> None:
        """Draw the menu and its drawables."""
        palette = self.get_palette()
        draw_fill(window, 0, 0, curses.LINES, curses.COLS, color_pair=palette.primary)

        super().draw(window)


# =====================================
#  Floating Menu
# =====================================


# class MenuFloating(Submenu):
#     """Floating Menu object."""

#     def __init__(
#         self,
#         y: int,
#         x: int,
#         h: int,
#         w: int,
#         default_selected: int | None = None,
#         auto_select_capturable_drawable_on_first_draw: Literal[
#             None, "First", "Last"
#         ] = None,
#         palette: Palette | None = None,
#     ):
#         """Floating menu object."""
#         super().__init__(
#             palette=None, auto_select_capturable_drawable_on_first_draw=None
#         )
#         self.y = y
#         self.x = x


# =====================================
#  Application
# =====================================
class Application:
    """Wrapper for the curses window, handles the main loop and user inputs."""

    def __init__(
        self,
        terminal_colors: Optional[TerminalColors] = None,
        color_pairs: ColorPairs = COLOR_PAIRS_BW,
        menus: list[Menu] = [],
    ) -> None:
        """Wrapper for the curses window, handles the main loop and user inputs.

        Args:
            terminal_colors (Optional[TerminalColors]): Terminal color palette to use. If None, the default terminal colors are used. Default is None.
            color_pairs (Optional[ColorPairs]): Color pairs to use. Default is COLOR_PAIRS_BW.
            menus (list[Menu]): List of menus to draw in the application. The selected menu is determined by self.selected_menu, which is 0 by default.
        """
        self.menus = menus
        self.terminal_colors = terminal_colors
        self.color_pairs = color_pairs

        self.selected_menu: int = 0
        self._running = False

    def draw(self, window: cwin) -> None:
        """Draw the UI."""
        self._check_selected_menu()

        self.menus[self.selected_menu].draw(window)
        # TODO: Add floating menus

        # TODO: TEMP
        draw_genstr(
            window,
            0,
            0,
            GenStr(f"COLS:{curses.COLS}, LINES:{curses.LINES}"),
            default_color_pair=-1,
        )

    def key_behaviour(self, key: int, window: cwin) -> None:
        """Handle key input."""
        self._check_selected_menu()

        if key == curses.KEY_RESIZE:  # Handle terminal resize
            h, w = window.getmaxyx()
            curses.resize_term(h, w)
        elif key == ord("q"):
            self._running = False  # Exit on 'q' key.
            return

        try:
            self.menus[self.selected_menu].key_behaviour(key)
        except Signal as signal:
            if isinstance(signal, SignalCaptureRemove):
                raise ValueError("A selected menu should never be exited from.")
            raise signal
        

    def _on_loop_start(self) -> None:
        """Behaviour to execute on the first draw of the UI."""
        # Check whether selected menu is valid
        self._check_selected_menu()

        # Colors
        self._init_colors()

    def _check_selected_menu(self) -> None:
        """Check if the selected menu index is valid."""
        if self.selected_menu < 0 or self.selected_menu >= len(self.menus):
            if len(self.menus) == 0:
                raise ValueError("No menus to draw.")
            raise ValueError("Selected menu index out of range.")

    def _init_colors(self) -> None:
        """Init colors."""
        curses.start_color()
        curses.use_default_colors()  # Default terminal colors, to override if custom terminal colors provided.

        if self.terminal_colors is not None:
            # Custom terminal colors provided
            if not curses.can_change_color():
                raise ValueError(
                    "Terminal does not support color changes, cannot initialize color palette."
                )
            if len(self.terminal_colors) > curses.COLORS:
                raise ValueError(
                    f"Too many terminal colors provided ({len(self.terminal_colors)}) for the terminal (max {curses.COLORS})."
                )

            for i, color in enumerate(self.terminal_colors):
                curses.init_color(i, color.r, color.g, color.b)

        # Custom color pairs
        for i, (fg, bg) in enumerate(self.color_pairs):
            curses.init_pair(
                i + 1, fg, bg
            )  # Color pair numbers start from 1 in curses.

    def _loop(self, window: cwin) -> None:
        """Main loop of the UI."""
        self._on_loop_start()

        self._running = True
        while self._running:
            try:
                # Draw
                window.erase()
                window.noutrefresh()
                self.draw(window)
                curses.doupdate()

                # Key handling
                key = window.getch()
                self.key_behaviour(key, window)
            except KeyboardInterrupt:
                self._running = False  # Exit

    def _start_curses(self, window: cwin) -> None:
        """Wrapped function to start curses application."""

        self._on_loop_start()
        self._loop(window)

    def start(self) -> None:
        """Main loop of the UI."""

        curses.wrapper(self._start_curses)


# =====================================
#  Other
# =====================================

# class MenuFloating(Menu):
#     """Floating Menu object."""

#     def __init__(
#         self, y: int, x: int, h: int, w: int, default_selected: int | None = None
#     ):
#         """Floating menu object."""
#         super().__init__(default_selected)
#         self.y = y
#         self.x = x


# class MenuFloatingCentered(MenuFloating):
#     """Centered floating Menu object."""

#     def __init__(self, h: int, w: int, default_selected: int | None = None):
#         y, x = ...
#         super().__init__(y, x, h, w, default_selected)
