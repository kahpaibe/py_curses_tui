import curses
from curses import window as cwin
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from typing import Literal, Optional, override
from enum import Enum

from .utils.draw_utils import draw_genstr, draw_fill
from .genstr import GenStr
from .utils.colors import (
    COLOR_PAIRS_BW,
    ColorPairs,
    TerminalColors,
    Palette,
    PALETTE_BW
)

# =====================================
#  Base Classes
# =====================================


class RedrawSignal(Exception): # TODO: to use
    """Exception to signal a redraw of the UI."""


class KeyBehaviourFlag(Enum):
    """Flag for key_behaviour."""

    SKIPPED = 0  # Key not used (e.g. no key behaviour)
    HANDLED = 1  # Key used (e.g. button press)
    EXIT = -1  # Ask to remove selection (e.g. navigate out)


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

    def _get_y_x(self) -> tuple[int, int]:
        """Get the absolute y and x coordinates of the drawable object, taking into account the parent drawables."""
        if self.parent is None:
            return (self.y, self.x)
        parent_y, parent_x = self.parent._get_y_x()
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

    def key_behaviour(self, key: int) -> KeyBehaviourFlag:
        """Behaviour of the Drawable in reponse to a key input.

        Args:
            - key (int): key to process

        Return (KeyBehaviourFlag):
            Flag to communicate how the key was handled.
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
            return PALETTE_BW # Default palette if no parent and no palette specified.

    def _on_first_draw(self) -> None:
        """Behaviour to execute on the first draw of the drawable object."""
        if self._first_draw:
            self._first_draw = False


class Submenu(Drawable):
    """Elementary unit for drawable navigation, draws and control drawables it contains."""

    @override
    def __init__(
        self,
        palette: Palette | None = None,
        auto_select_capturable_drawable_on_first_draw: Literal[
            None, "First", "Last"
        ] = None,
    ):
        """A submenu spanning all the window."""
        super().__init__(0, 0, parent=None, palette=palette)
        self.drawables: list[Drawable] = []
        self._selected_drawable_index: int = 0
        self._auto_select_capturable_drawable_on_first_draw = (
            auto_select_capturable_drawable_on_first_draw
        )

    def select_drawable(self, index: int) -> None:
        """Select a drawable by index. This is the expected way to define the selected drawable on application start."""
        self._selected_drawable_index = index
        self._check_selected_drawable()

    def get_selected_drawable_index(self) -> int:
        """Get the index of the currently selected drawable.

        Return (int):
            Index of the currently selected drawable.
        """
        self._check_selected_drawable()
        return self._selected_drawable_index

    @override
    def _on_first_draw(self) -> None:
        if self._auto_select_capturable_drawable_on_first_draw == "First":
            y, x = self._get_y_x()
            for i, drawable in enumerate(self.drawables):
                if drawable.capture(y, x):
                    self.select_drawable(i)
                    break
        elif self._auto_select_capturable_drawable_on_first_draw == "Last":
            y, x = self._get_y_x()
            for i in range(len(self.drawables) - 1, -1, -1):
                if self.drawables[i].capture(y, x):
                    self.select_drawable(i)
                    break

        return super()._on_first_draw()

    @override
    def draw(self, window: cwin) -> None:
        """Draw the menu and its drawables."""
        if self._first_draw:
            self._on_first_draw()

        for drawable in self.drawables:
            drawable.draw(window)

    @override
    def capture(self, y_prev: int, x_prev: int) -> bool:
        """Whether the Drawable can be selected."""
        y, x = self._get_y_x()
        if not self.drawables:  # If no drawable, cannot be captured.
            return False

        # TODO: via score / distance
        # TODO: for now, temp behaviour
        # Capture the last drawable if coming from the right or below.
        if x_prev > x or (x_prev == x and y_prev > y):
            self.select_drawable(len(self.drawables) - 1)
        else:  # Capture the first drawable if coming from the left or above, or if there are no drawables.
            self.select_drawable(0)

        return True  # Accept capture.

    @override
    def key_behaviour(self, key: int) -> KeyBehaviourFlag:
        """Behaviour of the Submenu in reponse to a key input.

        Args:
            - key (int): key to process

        Return (KeyBehaviourFlag):
            Flag to communicate how the key was handled.
        """
        if not self.drawables:
            return KeyBehaviourFlag.SKIPPED  # Nothing to do since there is no drawable.

        # Check selected drawable validity.
        self._check_selected_drawable()
        selected_drawable = self.drawables[self._selected_drawable_index]

        # Call selected drawable's key_behaviour
        flag = selected_drawable.key_behaviour(key)

        if flag is KeyBehaviourFlag.SKIPPED:
            return (
                KeyBehaviourFlag.SKIPPED
            )  # Key not captured by selected drawable, skip.
        elif flag is KeyBehaviourFlag.HANDLED:
            return KeyBehaviourFlag.HANDLED  # Key handled by selected drawable, exit.
        elif flag is KeyBehaviourFlag.EXIT:
            # Drawable wishes not to be captured anymore.
            # TODO: use score / distance
            # TODO: for now, temp behaviour
            # Find next capturing drawable.
            if key == curses.KEY_DOWN:
                # Go through the drawables until we find a capture-able one, or loop back to the start.
                prev_y, prev_x = selected_drawable._get_y_x()
                for i in range(self._selected_drawable_index + 1, len(self.drawables)):
                    if self.drawables[i].capture(prev_y, prev_x):
                        self.select_drawable(i)
                        return (
                            KeyBehaviourFlag.HANDLED
                        )  # Found a capture-able drawable, select it and exit.
                # Else no drawable found, try to remove capture
                return KeyBehaviourFlag.EXIT

            elif key == curses.KEY_UP:
                # Go through the drawables until we find a capture-able one, or loop back to the end.
                prev_y, prev_x = selected_drawable._get_y_x()
                for i in range(self._selected_drawable_index - 1, -1, -1):
                    if self.drawables[i].capture(prev_y, prev_x):
                        self.select_drawable(i)
                        return (
                            KeyBehaviourFlag.HANDLED
                        )  # Found a capture-able drawable, select it and exit.
                # Else no drawable found, try to remove capture
                return KeyBehaviourFlag.EXIT

        # else, nothing done
        return KeyBehaviourFlag.SKIPPED

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
        if self._selected_drawable_index < 0 or self._selected_drawable_index >= len(
            self.drawables
        ):
            raise ValueError("Selected drawable index out of range.")


class Menu(Submenu):
    """A submenu spanning all the window."""

    def __init__(self, palette: Palette | None = None, auto_select_capturable_drawable_on_first_draw: None | Literal['First'] | Literal['Last'] = None):
        """A menu spanning all the window.
        
        Palette:
            - primary: background color (background of the pair)"""
        super().__init__(palette=palette, auto_select_capturable_drawable_on_first_draw=auto_select_capturable_drawable_on_first_draw)

    @override
    def draw(self, window: cwin) -> None:
        """Draw the menu and its drawables."""
        palette = self.get_palette()
        draw_fill(window, 0, 0, curses.LINES, curses.COLS, color_pair=-palette.secondary)

        super().draw(window)


class App:
    """Wrapper for the curses window, handles the main loop and user inputs."""

    def __init__(
        self,
        terminal_colors: TerminalColors | None = None,
        color_pairs: ColorPairs = COLOR_PAIRS_BW,
        menus: list[Menu] = [],
    ) -> None:
        """Wrapper for the curses window, handles the main loop and user inputs.

        Args:
            terminal_colors (TerminalColors | None): Terminal color palette to use. If None, the default terminal colors are used. Default is None.
            color_pairs (ColorPairs | None): Color pairs to use. Default is COLOR_PAIRS_BW.
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
        draw_genstr(window, 0, 0, GenStr(f"COLS:{curses.COLS}, LINES:{curses.LINES}"), default_color_pair=-1)

    def key_behaviour(self, key: int, window: cwin) -> None:
        """Handle key input."""
        self._check_selected_menu()

        if key == curses.KEY_RESIZE: # Handle terminal resize
            h, w = window.getmaxyx()
            curses.resize_term(h, w)
        elif key == ord("q"):
            self._running = False  # Exit on 'q' key.
            return

        self.menus[self.selected_menu].key_behaviour(key)

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
