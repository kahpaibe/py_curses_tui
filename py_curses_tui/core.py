import curses
import curses.ascii
import logging
import os
import pathlib
from dataclasses import replace
from sys import platform
from typing import Any, Callable, Dict, List, Optional, Tuple, Type

from .drawables.animated_text import AnimatedText

# === import all the drawables and utility functions or constants ===
from .drawables.base_classes import (
    AttrStr,
    Choice,
    ColorPairs,
    ColorPalette,
    Drawable,
    DrawableContainer,
    GenStr,
    Hitbox,
    KeyCaptureDrawable,
    Submenu,
)
from .drawables.box import Box
from .drawables.button import Button
from .drawables.choose import Choose
from .drawables.color_setter import ColorSetter
from .drawables.dropdown import DropDown
from .drawables.file_explorer import FileExplorer
from .drawables.fill import Fill
from .drawables.item_list_submenu import ItemListSubmenu
from .drawables.multi_select import MultiSelect
from .drawables.rgb_preview import MAX_PAIRS, RGBPreview
from .drawables.scrollable_choose import ScrollableChoose
from .drawables.scrollable_container import ScrollableContainer
from .drawables.scrollable_multi_select import ScrollableMultiSelect
from .drawables.scrollable_textbox import ScrollableTextBox
from .drawables.scrollable_textdisplay import ScrollableTextDisplay
from .drawables.single_select import SingleSelect
from .drawables.text import Text
from .drawables.textbox import TextBox
from .drawables.textinput import TextInput
from .drawables.toggle import Toggle
from .drawables.wrapper_reset import WrapperReset
from .utility import (
    MAX_DELTA,
    CountDownObject,
    Point,
    calls,
    cp,
    cwin,
    inserted_text,
    set_value,
    try_self_call,
)

# ==== Color Palettes ====


def get_color_pairs() -> ColorPairs:
    """Enables definition after curses is initialized.
    Template in user_interface.py"""
    # === Custom colors ===
    # Curses' default colors go from 0 to 7. One may define custom colors up to curses.COLORS - 1
    # Please not that some objects such as ColorDisplay use the shared curses.COLORS - 1 by default
    default_colors = [
        curses.COLOR_BLACK,
        curses.COLOR_RED,
        curses.COLOR_GREEN,
        curses.COLOR_YELLOW,
        curses.COLOR_BLUE,
        curses.COLOR_MAGENTA,
        curses.COLOR_CYAN,
        curses.COLOR_WHITE,
    ]
    maxi = max(default_colors)  # max index of default defined colors
    GRAY = maxi + 1  # Grey of index maxi + 1
    curses.init_color(GRAY, 500, 500, 500)

    # === Color pairs ====
    # == Black background ==
    pairs_black = [
        (curses.COLOR_RED, curses.COLOR_BLACK),  # 1
        (curses.COLOR_GREEN, curses.COLOR_BLACK),  # 2
        (curses.COLOR_YELLOW, curses.COLOR_BLACK),  # 3 inv(Warning unsaturated)
        (curses.COLOR_BLUE, curses.COLOR_BLACK),  # 4
        (curses.COLOR_MAGENTA, curses.COLOR_BLACK),  # 5
        (curses.COLOR_CYAN, curses.COLOR_BLACK),  # 6
        (curses.COLOR_WHITE, curses.COLOR_BLACK),  # 7
    ]
    # == White background ==
    pairs_white = [
        (curses.COLOR_BLACK, curses.COLOR_WHITE),  # 8
        (curses.COLOR_RED, curses.COLOR_WHITE),  # 9 (Error) + inv(Error unsaturated)
        (curses.COLOR_GREEN, curses.COLOR_WHITE),  # 10
        (curses.COLOR_YELLOW, curses.COLOR_WHITE),  # 11 (Warning)
        (curses.COLOR_BLUE, curses.COLOR_WHITE),  # 12 (Info) + Inv(Info unsaturated)
        (curses.COLOR_MAGENTA, curses.COLOR_WHITE),  # 13
        (curses.COLOR_CYAN, curses.COLOR_WHITE),  # 14
    ]
    # == Other ==
    pairs_other = [
        # = With custom colors =
        (GRAY, curses.COLOR_BLACK),  # 15
        (GRAY, curses.COLOR_WHITE),  # 16
        # = Other =
        (curses.COLOR_RED, curses.COLOR_BLUE),  # 17
    ]

    pairs = pairs_black + pairs_white + pairs_other

    return ColorPairs(pairs)


# ==== Management objects ====


class Menu(DrawableContainer):
    """A menu which contains Drawable objects, one of which is displayed at a time by the UserInterface."""

    def __init__(
        self,
        palette: Optional[ColorPalette] = ColorPalette(),
        default_selected: Tuple[int, int] = (0, 0),
    ):
        """A menu which contains Drawable objects, one of which is displayed at a time by the UserInterface.

        Args:
            palette (Optional[ColorPalette], optional): color palette. Defaults to ColorPalette().
            default_selected (Tuple[submenu:int, id:int], optional): default selected object. Defaults to (0, 0).
        """
        super().__init__(0, 0, None, palette)
        self._submenus: List[Submenu] = []  # submenus
        self.selected_submenu = 0  # selected submenu
        self._default_selected = default_selected
        self._first_draw = False  # whether it was drawn once. Sort of init

    def handle_submenu_goto(self, origin: Tuple[int, int], direction: int) -> bool:
        """Handle the switch between KeyCaptureDrawables.

        origin = (y:int, x:int) origin coordinates
        direction 0:down, 1: right, 2:up, 3:left movement direction"""

        n = self.selected_submenu
        current_submenu = self._submenus[n]
        if direction == 0:  # go down
            # get closest submenu
            m = min(
                range(len(self._submenus)),
                key=lambda i: self._submenus[i].distance_from(origin, 0),
            )

            if m == n:
                return False

            else:  # otherwise
                current_submenu.capture_remove(direction)
                self.selected_submenu = m
                self._submenus[m].capture_take(origin, direction)
                return True
        elif direction == 1:  # go right
            # get closest submenu
            m = min(
                range(len(self._submenus)),
                key=lambda i: self._submenus[i].distance_from(origin, 1),
            )
            if m == n:
                return False

            else:
                current_submenu.capture_remove(direction)
                self.selected_submenu = m
                self._submenus[m].capture_take(origin, 1)
                return True
        elif direction == 2:  # go up
            # get closest submenu
            m = min(
                range(len(self._submenus)),
                key=lambda i: self._submenus[i].distance_from(origin, 2),
            )
            if m == n:
                return False

            else:
                current_submenu.capture_remove(direction)
                self.selected_submenu = m
                self._submenus[m].capture_take(origin, direction)
                return True
        elif direction == 3:  # go left
            # get closest submenu
            m = min(
                range(len(self._submenus)),
                key=lambda i: self._submenus[i].distance_from(origin, 3),
            )
            if m == n:
                return False

            else:
                current_submenu.capture_remove(direction)
                self.selected_submenu = m
                self._submenus[m].capture_take(origin, direction)
                return True

    def add_key_capture_drawable(
        self,
        kcd: KeyCaptureDrawable,
        submenu: int = 0,
        palette: Optional[ColorPalette] = None,
    ) -> None:
        """Add a KeyCaptureDrawable to the menu.

        Args:
            kcd (KeyCaptureDrawable): object to add
            submenu (int, optional): 'submenu' index. Defaults to 0.
            palette (Optional[ColorPalette], optional): color palette. Defaults to None.

        If the kcd object does not have a parent, the menu will be set as its parent.
        If the kcd object does not have a palette, the menu's palette will be set as its palette.

        About submenus:
            Groups the KeyCaptureDrawables for better navigation (example: a column, a line, a group).
            Navigation will prioritize navigation inside a submenu, then between submenu.

        Note: this is the only good way to add a KeyCaptureDrawable.
        For example:
            box.add(obj)
        would not make obj capture anything. it should be replaced by:
            obj.parent = box
            menu.add_key_capture_drawable(obj)"""
        if not kcd.parent:
            kcd.parent = self  # container is parent
        if kcd.palette is None:
            kcd.palette = palette  # set palette container palette for child

        try:
            self._submenus[submenu].add(kcd)
        except IndexError:
            new_submenu = Submenu()
            new_submenu.capture_goto = self.handle_submenu_goto
            new_submenu.add(kcd)
            self._submenus.append(new_submenu)
            if submenu > len(self._submenus) - 1:
                raise ValueError(
                    f"given submenu {submenu} is out of range, {len(self._submenus) = }"
                )

    def draw(self, window: cwin) -> None:
        if not self._first_draw:
            self._do_first_draw()

        for obj in self.drawables:
            obj.draw(window)
        for submenu in self._submenus:
            submenu.draw(window)

    def key_behaviour(self, key: int) -> None:
        if len(self._submenus) > 0:
            self._submenus[self.selected_submenu].key_behaviour(key)

        for obj in self.drawables:  # children's key behaviour, non capture
            obj.key_behaviour(key)

    def should_bypass(self) -> bool:
        try:
            return self._submenus[self.selected_submenu].should_bypass()
        except IndexError:
            return False

    def _do_first_draw(self) -> None:
        """Initial init"""
        self._first_draw = True

        # select the default selected
        self.select_key_capture_drawable(self._default_selected[0], self._default_selected[1])

    def clear(self, reset_first_draw: bool = True) -> None:
        """Clear all the drawables and submenus.

        Args:
            reset_first_draw (bool, optional): whether to reset the first draw flag. Defaults to True.
        """
        self.drawables.clear()
        self._submenus.clear()
        if reset_first_draw:
            self._first_draw = False

    def get_submenus(self) -> List[Submenu]:
        """Get all submenus."""
        return self._submenus

    def get_submenu(self, submenu_index: int) -> Submenu:
        """Get current selected submenu."""
        return self._submenus[submenu_index]

    def set_submenu(self, submenu: Submenu, submenu_index: int) -> None:
        """Replace the submenu at given index."""
        submenu.capture_goto = self.handle_submenu_goto
        if submenu_index < len(self._submenus):
            self._submenus[submenu_index] = submenu
        elif submenu_index == len(self._submenus):  # create new submenu
            self._submenus.append(submenu)
        else:
            raise ValueError(
                f"submenu_index {submenu_index} is out of range, {len(self._submenus) = }"
            )

    def select_key_capture_drawable(self, submenu_index: int, index: int) -> None:
        """Select a KeyCaptureDrawable at given position (submenu, index)."""
        for i in range(len(self._submenus)):
            if i == submenu_index:
                self._submenus[submenu_index].activate(index)
                self.selected_submenu = submenu_index
            else:
                self._submenus[i].activate(-1)  # disable

    def set_on_update(
        self,
        on_update: Callable[[Drawable], Any] | None = None,
        exclude: List[Drawable] = [],
    ) -> None:
        """Set the on_update function to all inside objects (except excluded objects). Will skip objects with on_update already define.

        Args:
            on_update (Callable[[Drawable], Any], optional): on_update function. Defaults to None.
            exclude (List[Drawable], optional): objects to exclude. Defaults to []."""

        for submenu in self._submenus:
            if submenu not in exclude:
                submenu.set_on_update(on_update, exclude)
        for obj in self.drawables:
            if obj not in exclude:
                if obj.on_update is None:
                    obj.set_on_update(on_update)

    def get_selected_index(self) -> Tuple[int, int]:
        """Returns selected kcd index and submenu index. Tuple[submenu:int, id:int]"""
        try:
            return (self.selected_submenu, self._submenus[self.selected_submenu]._selected)
        except IndexError:
            return (-1, -1)

    def get_selected_kcd(self) -> KeyCaptureDrawable | None:
        """Returns selected kcd, or None if none selected."""
        if self.selected_submenu < 0:
            return None
        sb = self._submenus[self.selected_submenu]
        if sb._selected < 0:
            return None
        return sb._kcds[sb._selected]


class UserInterface:
    """The main user interface object. Contains menus and handles the main loop."""

    def __init__(
        self,
        stdscr: cwin,
        color_pairs: ColorPairs,
        menus: Dict[str, Menu],
        default_menu: str = "",
        min_height: int = 24,
        min_width: int = 80,
        logger: Optional[logging.Logger] = None,
    ):
        """The main user interface object. Contains menus and handles the main loop.
        Initializes curses.

        Args:
            stdscr: curses standard screen
            color_pairs (ColorPairs): color pairs
            menus (Dict[str, Menu]): menus to display
            default_menu (str, optional): default menu. Defaults to "" : any of the given menus.

        Example usage:
            def main(stdscr):
                color_pairs = UI.get_color_pairs() # initialize color pairs
                color_palette = UI.ColorPalette() # default color palette
                color_palette2 = UI.ColorPalette(text=3) # alternative color palette

                main_menu = UI.Menu(color_palette) # main menu
                menu2 = UI.Menu(color_palette2) # alternative menu
                menus = {"main": main_menu, "menu2": menu2} # the menus

                ui = UI.UserInterface(stdscr, color_pairs, menus) # create the user interface

                ui.ui_loop() # start the main loop

            if __name__ == "__main__":
                curses.wrapper(main)

        Notes:
            One may also specify custom exception handlers to catch specific exceptions during the execution of ui.draw() method by adding them to the ui.exception_handlers dictionary.
            Example:
                ui.exception_handlers[ZeroDivisionError] = lambda e: ui.info(f"ZeroDivisionError detected!: {e}")
        """
        if platform != "win32":
            curses.set_escdelay(25)  # set curses delay before emitting 'Esc' key to 25 ms
        if len(menus) <= 0:
            raise ValueError("menus must have at least one element")
        if len(default_menu) == 0:
            self.current_menu: str = next(iter(menus))  # pick one menu if none specified
        else:
            if default_menu not in menus:
                raise ValueError("default_menu must be a key in menus left empty")
            self.current_menu: str = default_menu
        self.menus: Dict[str, Menu] = menus
        self.menus_top: List[Menu] = []  # menus to draw on top of everything else

        self.stdscr = stdscr
        self.logger: logging.Logger = logger

        self.height = min_height
        self.width = min_width
        self.y = 0
        self.x = 0

        self.running = False  # whether the ui is running its loop
        self.interrupted = (
            False  # turns True is the ui was forcibly interrupted (KeyboardInterrupt)
        )

        self._menu_too_small = Menu()  # Menu to show when the window is too small
        self._text_menu_too_small = Text(GenStr(""), 0, 0, -9, attributes=[curses.A_BOLD])
        self._menu_too_small.add(self._text_menu_too_small)
        self._init_colors(color_pairs)

        self.exception_handlers: Dict[Type[BaseException], Callable[[BaseException], None]] = (
            {}
        )  # custom exception handlers

    def _init_colors(self, color_pairs: ColorPairs) -> None:
        curses.curs_set(0)  # Hide cursor
        curses.start_color()
        for i in range(0, len(color_pairs.pairs)):
            curses.init_pair(i + 1, color_pairs.pairs[i][0], color_pairs.pairs[i][1])

    def draw(self, window: cwin) -> None:  # draw the screen
        row, col = self.stdscr.getmaxyx()
        if row < self.height or col < self.width:  # if too small
            if row > 0 and col > 0:
                self._text_menu_too_small.set_text(
                    f"Warning ! Window size is too small.\n(minimum: {self.width}x{self.height}, current:{col}x{row})"
                )
                try:
                    self._menu_too_small.draw(window)
                    self.stdscr.refresh()
                except Exception:
                    pass  # if cannot draw
        else:
            self.menus[self.current_menu].draw(window)  # draw current menu
            self.stdscr.noutrefresh()

            for menu in self.menus_top:  # draw menu stack on top, -1 is the top one
                menu.draw(window)

    def key_behaviour(self, key: int) -> None:
        if key == curses.KEY_RESIZE:  # Avoid crash of resize (win)
            h, w = self.stdscr.getmaxyx()
            curses.resize_term(h, w)
        if (
            key == ord("q")
            and self.menus[self.current_menu].should_bypass()
            and (
                (len(self.menus_top) > 0 and self.menus_top[-1].should_bypass())
                or len(self.menus_top) == 0
            )
        ):  # Exit on 'q' key press
            self.stop()
            self.interrupted = True
        else:
            if len(self.menus_top) == 0:
                self.menus[self.current_menu].key_behaviour(key)
            else:  # len > 0 # key behaviour of top menu
                self.menus_top[-1].key_behaviour(key)

    def add_menu(self, menu: Menu, name: str) -> None:
        """Add a menu to the menus dictionary."""
        if name in self.menus:
            raise ValueError(f"Menu '{name}' already exists.")
        self.menus[name] = menu

    def set_menu(self, menu: str) -> None:
        """Set the current menu to the given menu."""
        if menu in self.menus:
            self.current_menu = menu
            self.update()
        else:
            self.error(f"Menu '{menu}' does not exist.")

    def get_hw(self) -> Tuple[int, int]:
        """Get the height and width of the screen."""
        return (self.height, self.width)

    def stop(self) -> None:
        """Stop the main loop."""
        self.running = False

    def ui_loop(self) -> None:
        """Start the main loop.

        The main loop may be stopped calling the stop() method.
        Pressing the 'q' key will also stop the loop."""
        self.stdscr.clear()

        self.running = True

        while self.running:

            try:
                self.stdscr.erase()
                self.stdscr.noutrefresh()
                self.draw(self.stdscr)
                curses.doupdate()
                # Handle user input
                if self.running:  # if still running
                    key = self.stdscr.getch()
                    self.key_behaviour(key)
            except KeyboardInterrupt:
                self.stop()
                self.interrupted = True
                if self.logger:
                    self.logger.info("KeyboardInterrupt")
            except curses.error as e:
                raise curses.error(f"Curses (drawing) related error: {e}") from e
            except tuple([key for key in self.exception_handlers]) as e:
                # custom exception handling
                handler = self.exception_handlers[type(e)]
                handler(e)
            except Exception as e:
                # Other exceptions
                raise e from e
                if self.logger:
                    self.logger.error(f"An error occured during loop:\n\n{e}")
                self.clear_top()
                self.error(f"An error occured during loop:\n\n{e}")

    def add_top(self, menu: Menu) -> None:
        """Add a menu to the top of the stack.

        The menu will be drawn on top of everything else (will capture all key events if self.menu_top_do_capture is True).
        """
        self.menus_top.append(menu)

    def clear_top(self) -> None:
        """Clear all menus drawn on top."""
        self.menus_top.clear()

    def pop_top(self) -> None:
        """Removes top menu."""
        self.menus_top.pop(-1)

    def pop_up(
        self,
        lines: str,
        actions: List[Tuple[str, Callable]],
        title: str = "",
        default_selected: int = 0,
        palette: Optional[ColorPalette] = ColorPalette(
            text=12, button_unselected=-16, button_selected=-12, box=12, cursor=14
        ),
    ) -> None:
        """Show a pop up window.

        Args:
            lines (str): text to display
            actions (List[Tuple[str, Callable]]): list of actions to execute. The first action will be executed on 'Enter' key press.
            title (str, optional): title of the pop up. Defaults to "".
            default_selected (int, optional): default selected button, from 0th to last. Defaults to 0.
            palette (Optional[ColorPalette], optional): color palette. Defaults to ColorPalette(text=12, button_unselected=-16, button_selected=-12, box=12, cursor=-12).

        For the actions, a self argument may be provided, referring to the UserInterface object.
        Example:
            actions = [("OK", lambda selfo: print(selfo.menus))] # where selfo is the UserInterface object
        """
        # === Create the menu ===
        if len(actions) == 0 or len(actions) == 1:
            m = Menu(palette, default_selected=(0, 0))
        elif len(actions) == 2:
            m = Menu(palette, default_selected=(default_selected, 0))
        else:  # more than 2 actions
            m = Menu(palette, default_selected=(0, 0))

        ls = [] if len(lines) == 0 else lines.split("\n")
        h = len(ls)
        mw = max(len(line) for line in ls) + 4
        w = mw if mw > 30 else 30
        h += 4 if len(actions) > 0 else 2
        h += len(actions) - 1 if len(actions) > 2 else 0  # if list of actions

        rows, cols = self.height, self.width

        box = Box(rows // 2 - h // 2, cols // 2 - w // 2, h, w, palette)
        # box = Box(5, 10, h, w, palette)
        m.add(box)
        if len(title) > 0:
            m.add(
                Text(
                    title,
                    0,
                    (w - len(title)) // 2,
                    palette.text,
                    parent=box,
                    attributes=[curses.A_BOLD],
                )
            )
        for i, line in enumerate(lines.split("\n")):
            m.add(Text(line, i + 1, 2, palette.text, width=w - 4, centered=True, parent=box))

        # == Add buttons ==
        if len(actions) == 0:
            m.add_key_capture_drawable(
                Button(
                    "OK",
                    h - 2,
                    2,
                    lambda: (self.pop_top(), self.stdscr.erase()),
                    width=w - 4,
                    centered=True,
                    parent=box,
                    palette=palette,
                )
            )
        elif len(actions) == 1:
            m.add_key_capture_drawable(
                Button(
                    actions[0][0],
                    h - 2,
                    2,
                    lambda: (
                        self.pop_top(),
                        self.stdscr.erase(),
                        try_self_call(self, actions[0][1]),
                    ),
                    width=w - 4,
                    centered=True,
                    parent=box,
                    palette=palette,
                ),
                0,
            )
        elif len(actions) == 2:
            m.add_key_capture_drawable(
                Button(
                    actions[0][0],
                    h - 2,
                    2,
                    lambda: (
                        self.pop_top(),
                        self.stdscr.erase(),
                        try_self_call(self, actions[0][1]),
                    ),
                    width=(w - 5) // 2,
                    centered=True,
                    parent=box,
                    palette=palette,
                ),
                0,
            )
            m.add_key_capture_drawable(
                Button(
                    actions[1][0],
                    h - 2,
                    w // 2 + 1,
                    lambda: (
                        self.pop_top(),
                        self.stdscr.erase(),
                        try_self_call(self, actions[1][1]),
                    ),
                    width=(w - 5) // 2,
                    centered=True,
                    parent=box,
                    palette=palette,
                ),
                1,
            )
        else:  # for more than 3 actions, add a Choose

            choices = []
            for i in range(len(actions)):

                def full_action(selfo: Choose, duo: Callable = actions[i]) -> None:
                    self.pop_top(),
                    self.stdscr.erase(),
                    try_self_call(self, duo[1]),

                choices.append(Choice(actions[i][0], full_action))

            m.add_key_capture_drawable(
                Choose(
                    h - 1 - len(actions) + box.y,
                    2 + box.x,
                    choices,
                    palette=palette,
                )
            )

        # === activate the pop up ===
        self.add_top(m)

    def info(
        self,
        text: str,
        palette: Optional[ColorPalette] = ColorPalette(
            text=12, button_unselected=-16, button_selected=-12, box=12
        ),
    ) -> None:
        """Shows an 'Info' pop up window.

        Args:
            text (str): text to display in the pop up.
            palette (Optional[ColorPalette], optional): color palette. Defaults to ColorPalette(text=12, button_unselected=-16, button_selected=-12, box=12).
        """
        if self.logger:
            self.logger.info(f"{text}")

        actions = [("OK", lambda: None)]
        self.pop_up(text, actions, " INFO ", 0, palette)

    def warning(
        self,
        text: str,
        palette: Optional[ColorPalette] = ColorPalette(
            text=11, button_selected=-16, box=11, cursor=-11
        ),
    ) -> None:
        """Shows an 'Warning' pop up window.

        Args:
            text (str): text to display in the pop up.
            palette (Optional[ColorPalette], optional): color palette. Defaults to ColorPalette(text=11, button_selected=-16, box=11, cursor=-11).
        """
        if self.logger:
            self.logger.warning(f"{text}")

        actions = [("OK", lambda: None)]
        self.pop_up(text, actions, " WARNING ", 0, palette)

    def error(
        self,
        text: str,
        palette: Optional[ColorPalette] = ColorPalette(
            text=9, button_selected=-16, box=9, cursor=-9
        ),
    ) -> None:
        """Shows an 'Error' pop up window.

        Args:
            text (str): text to display in the pop up.
            palette (Optional[ColorPalette], optional): color palette. Defaults to ColorPalette(text=9, button_selected=-16, box=-9, cursor=-9).
        """
        if self.logger:
            self.logger.error(f"{text}")

        actions = [("OK", lambda selfo: None), ("Quit", self.stop)]
        self.pop_up(text, actions, " ERROR ", 1, palette)

    def critical_error(
        self,
        text: str,
        palette: Optional[ColorPalette] = ColorPalette(
            text=9, button_selected=-16, box=-9, cursor=-9
        ),
    ) -> None:
        """Shows an 'Critical error' pop up window. The program will stop.

        Args:
            text (str): text to display in the pop up.
            palette (Optional[ColorPalette], optional): color palette. Defaults to ColorPalette(text=9, button_selected=-16, box=-9, cursor=-9).
        """
        if self.logger:
            self.logger.critical(f"{text}")

        actions = [("Quit", self.stop)]
        self.pop_up(text, actions, " CRITICAL ERROR ", 0, palette)

    def prompt(
        self,
        lines: str,
        title: str = "",
        input_max_length: int = 1,
        confirm_action: Callable = (lambda: None),
        default_value: str = "",
        palette: Optional[ColorPalette] = ColorPalette(
            text=12, button_unselected=-16, button_selected=-12, box=12
        ),
    ) -> None:
        """Show a prompt to ask for user input.

        Args:
            lines (str): text to display in the prompt.
            title (str, optional): title of the prompt. Defaults to "".
            input_max_length (int, optional): maximum length of the input. Defaults to 1.
            confirm_action (Callable, optional): action to execute on 'Confirm' button press. Defaults to (lambda: None).
            palette (Optional[ColorPalette], optional): color palette. Defaults to ColorPalette(text=12, button_unselected=-16, button_selected=-12, box=12).

        In given confirm_action, the self=text_content object is passed as argument (optional).
        Usage example: confirm_action=lambda text: print(text) # where text is the TextInput's text
        """
        # === Create the menu ===
        m = Menu(palette)

        ls = [] if len(lines) == 0 else lines.split("\n")
        h = len(ls) + 6
        mw = max(len(line) for line in ls) + 4
        w = max([mw, input_max_length + 4, 30])
        self.input_max_length = input_max_length

        rows, cols = self.height, self.width

        box = Box(rows // 2 - h // 2, cols // 2 - w // 2, h, w, palette)

        m.add(box)
        if len(title) > 0:  # add title
            m.add(
                Text(
                    title,
                    0,
                    (w - len(title)) // 2,
                    palette.text,
                    parent=box,
                    attributes=[curses.A_BOLD],
                )
            )
        for i, line in enumerate(lines.split("\n")):
            m.add(Text(line, i + 1, 2, palette.text, width=w - 4, centered=True, parent=box))

        # == Add buttons ==
        textinput = TextInput(h - 4, 2, width=self.input_max_length, parent=box, palette=palette)
        textinput.activate()  # activate the textinput
        m.add_key_capture_drawable(textinput, submenu=0)
        m.add_key_capture_drawable(
            Button(
                "Confirm",
                h - 2,
                2,
                lambda: (
                    self.pop_top(),
                    self.stdscr.erase(),
                    try_self_call(textinput.get_text(), confirm_action),
                ),
                width=w // 2 - 3,
                centered=True,
                parent=box,
            ),
            submenu=1,
        )
        m.add_key_capture_drawable(
            Button(
                "Cancel",
                h - 2,
                w // 2 + 2,
                calls(self.pop_top, self.stdscr.erase),
                width=w // 2 - 3,
                centered=True,
                parent=box,
            ),
            submenu=1,
        )

        if len(default_value) > 0:
            textinput.set_text(default_value)

        # === activate the pop up ===
        self.add_top(m)

    def confirm(
        self,
        lines: str,
        title: str = "",
        confirm_action: Callable = (lambda: None),
        palette: Optional[ColorPalette] = ColorPalette(
            text=12, button_unselected=-16, button_selected=-12, box=12
        ),
    ) -> None:
        """Show a confirmation prompt, executes given confirm_action on 'Confirm' button press or do nothing on 'Cancel'.

        Args:
            lines (str): text to display in the prompt.
            title (str, optional): title of the prompt. Defaults to "".
            confirm_action (Callable, optional): action to execute on 'Confirm' button press. Defaults to (lambda: None).
            palette (Optional[ColorPalette], optional): color palette. Defaults to ColorPalette(text=12, button_unselected=-16, button_selected=-12, box=12).

        In given confirm_action, the self=text_content object is passed as argument (optional).
        Usage example: confirm_action=lambda text: print(text) # where text is the TextInput's text
        """

        # === Create the menu ===
        m = Menu(palette)

        ls = [] if len(lines) == 0 else lines.split("\n")
        h = len(ls) + 4
        mw = max(len(line) for line in ls) + 4
        w = max([mw, 30])

        rows, cols = self.height, self.width

        box = Box(rows // 2 - h // 2, cols // 2 - w // 2, h, w, palette)

        m.add(box)
        if len(title) > 0:  # add title
            m.add(
                Text(
                    title,
                    0,
                    (w - len(title)) // 2,
                    palette.text,
                    parent=box,
                    attributes=[curses.A_BOLD],
                )
            )
        for i, line in enumerate(lines.split("\n")):
            m.add(Text(line, i + 1, 2, palette.text, width=w - 4, centered=True, parent=box))

        # == Add buttons ==
        m.add_key_capture_drawable(
            Button(
                "Confirm",
                h - 2,
                2,
                calls(
                    self.pop_top,
                    self.stdscr.erase,
                    lambda: try_self_call(self, confirm_action),
                ),
                width=w // 2 - 3,
                centered=True,
                parent=box,
            ),
            submenu=0,
        )
        m.add_key_capture_drawable(
            Button(
                "Cancel",
                h - 2,
                w // 2 + 2,
                calls(self.pop_top, self.stdscr.erase),
                width=w // 2 - 3,
                centered=True,
                parent=box,
            ),
            submenu=0,
        )

        # === activate the pop up ===
        self.add_top(m)

    def browse_file(
        self,
        lines: str = "Please select a file",
        title: str = "BROWSE FILES",
        items_height: int = 10,
        items_width: int = 60,
        select_action: Callable[[str], Any] = (lambda a="": None),
        filter_: Optional[List[str]] = [],
        palette: Optional[ColorPalette] = ColorPalette(
            text=12, button_unselected=-16, button_selected=-12, box=12
        ),
    ) -> None:
        """Prompt to browse the file system to select a file.

        Args:
            lines (str, optional): text to display in the prompt. Defaults to "Please select a directory".
            title (str, optional): title of the prompt. Defaults to "BROWSE DIRECTORIES".
            items_height (int, optional): height of the file explorer. Defaults to 10.
            items_width (int, optional): width of the file explorer. Defaults to 60.
            select_action (Callable[[str], Any], optional): action to execute on file selection. Defaults to (lambda a="": None).
            palette (Optional[ColorPalette], optional): color palette. Defaults to ColorPalette(text=12, button_unselected=-16, button_selected=-12, box=12).

        ColorPalette:
            explorer_prompt_path: current path color
            explorer_prompt_dim: dimmed text color
            explorer_prompt_file: files color
            explorer_prompt_directory: directories color
            explorer_prompt_dots: dots color
            explorer_prompt_selected: selected item color
            explorer_prompt_scrollbar: scrollbar color

        The select_action action may be provided with a str argument.
        Example:
            select_action = lambda s: print(f'You selected the file {s} !') # where s in the path of the selected file or directory.
        """
        palette: ColorPalette = replace(palette)  # copy palette

        # === Create the menu ===
        palette.file_explorer_path = palette.explorer_prompt_path
        palette.file_explorer_dim = palette.explorer_prompt_dim
        palette.file_explorer_file = palette.explorer_prompt_file
        palette.file_explorer_directory = palette.explorer_prompt_directory
        palette.file_explorer_dots = palette.explorer_prompt_dots
        palette.file_explorer_selected = palette.explorer_prompt_selected
        palette.scrollbar = palette.explorer_prompt_scrollbar

        m = Menu(palette)

        ls = [] if len(lines) == 0 else lines.split("\n")
        h = len(ls) + items_height + 2 + 5
        w = max([items_width + 6, 30])

        rows, cols = self.height, self.width

        box = Box(rows // 2 - h // 2, cols // 2 - w // 2, h, w, palette)

        m.add(box)
        if len(title) > 0:  # add title
            m.add(
                Text(
                    title,
                    0,
                    (w - len(title)) // 2,
                    palette.text,
                    parent=box,
                    attributes=[curses.A_BOLD],
                )
            )
        for i, line in enumerate(lines.split("\n")):
            m.add(Text(line, i + 1, 2, palette.text, width=w - 4, centered=True, parent=box))

        # == Add file explorer ==
        fe = FileExplorer(
            len(ls) + 2,
            2,
            items_height + 2,
            items_width + len(FileExplorer.file_symbol),
            False,
            file_or_dot_action=lambda s: (self.pop_top(), select_action(s)),
            ui=self,
            filter_=filter_,
            parent=box,
            palette=palette,
        )
        m.add_key_capture_drawable(fe, submenu=0)

        # == Add buttons ==
        m.add_key_capture_drawable(
            Button(
                "Cancel",
                h - 2,
                w // 4,
                calls(self.pop_top, self.stdscr.erase),
                width=w // 2 - 2,
                centered=True,
                parent=box,
            ),
            submenu=0,
        )

        # === activate the pop up ===
        self.add_top(m)

    def browse_directory(
        self,
        lines: str = "Please select a directory",
        title: str = "BROWSE DIRECTORIES",
        items_height: int = 10,
        items_width: int = 60,
        select_action: Callable[[str], Any] = (lambda a="": None),
        palette: Optional[ColorPalette] = ColorPalette(
            text=12, button_unselected=-16, button_selected=-12, box=12
        ),
    ) -> None:
        """Prompt to browse the file system to select a directory.

        Args:
            lines (str, optional): text to display in the prompt. Defaults to "Please select a directory".
            title (str, optional): title of the prompt. Defaults to "BROWSE DIRECTORIES".
            items_height (int, optional): height of the file explorer. Defaults to 10.
            items_width (int, optional): width of the file explorer. Defaults to 60.
            select_action (Callable[[str], Any], optional): action to execute on file selection. Defaults to (lambda a="": None).
            palette (Optional[ColorPalette], optional): color palette. Defaults to ColorPalette(text=12, button_unselected=-16, button_selected=-12, box=12).

        ColorPalette:
            explorer_prompt_path: current path color
            explorer_prompt_dim: dimmed text color
            explorer_prompt_file: files color
            explorer_prompt_directory: directories color
            explorer_prompt_dots: dots color
            explorer_prompt_selected: selected item color
            explorer_prompt_scrollbar: scrollbar color

        The select_action action may be provided with a str argument.
        Example:
            select_action = lambda s: print(f'You selected the file {s} !') # where s in the path of the selected file or directory.
        """
        palette: ColorPalette = replace(palette)  # copy palette

        # === Create the menu ===
        palette.file_explorer_path = palette.explorer_prompt_path
        palette.file_explorer_dim = palette.explorer_prompt_dim
        palette.file_explorer_file = palette.explorer_prompt_file
        palette.file_explorer_directory = palette.explorer_prompt_directory
        palette.file_explorer_dots = palette.explorer_prompt_dots
        palette.file_explorer_selected = palette.explorer_prompt_selected
        palette.scrollbar = palette.explorer_prompt_scrollbar

        m = Menu(palette)

        ls = [] if len(lines) == 0 else lines.split("\n")
        h = len(ls) + items_height + 2 + 5
        w = max([items_width + 6, 30])

        rows, cols = self.height, self.width

        box = Box(rows // 2 - h // 2, cols // 2 - w // 2, h, w, palette)

        m.add(box)
        if len(title) > 0:  # add title
            m.add(
                Text(
                    title,
                    0,
                    (w - len(title)) // 2,
                    palette.text,
                    parent=box,
                    attributes=[curses.A_BOLD],
                )
            )
        for i, line in enumerate(lines.split("\n")):
            m.add(Text(line, i + 1, 2, palette.text, width=w - 4, centered=True, parent=box))

        # == Add file explorer ==
        fe = FileExplorer(
            len(ls) + 2,
            2,
            items_height + 2,
            items_width + len(FileExplorer.file_symbol),
            True,
            file_or_dot_action=lambda s: (self.pop_top(), select_action(s)),
            ui=self,
            parent=box,
            palette=palette,
        )
        m.add_key_capture_drawable(fe, submenu=0)

        # == Add buttons ==
        m.add_key_capture_drawable(
            Button(
                "Cancel",
                h - 2,
                w // 4,
                calls(self.pop_top, self.stdscr.erase),
                width=w // 2 - 2,
                centered=True,
                parent=box,
            ),
            submenu=0,
        )

        # === activate the pop up ===
        self.add_top(m)

    def save_as(
        self,
        lines: str = "",
        title: str = "SAVE AS",
        items_height: int = 10,
        items_width: int = 60,
        save_action: Callable[[str], Any] = (lambda a="": None),
        extensions: None | str | List[str] = None,
        palette: Optional[ColorPalette] = ColorPalette(
            text=12, button_unselected=-16, button_selected=-12, box=12
        ),
    ) -> None:
        """Prompt to save a file.

        Args:
            lines (str, optional): text to display in the prompt. Defaults to "".
            title (str, optional): title of the prompt. Defaults to "SAVE AS".
            items_height (int, optional): height of the file explorer. Defaults to 10.
            items_width (int, optional): width of the file explorer. Defaults to 60.
            save_action (Callable[[str], Any], optional): action to execute on file save. Defaults to (lambda a="": None).
            extensions (None | str | List[str], optional): file extensions to filter. Defaults to None.
            palette (Optional[ColorPalette], optional): color palette. Defaults to ColorPalette(text=12, button_unselected=-16, button_selected=-12, box=12).

        About save_action:
            Should be a callable that would to the action of saving as, which would take one argument file_path:str.
            Example: save_action = lambda file_path: self.info(f"Saving file as {file_path}")
        """

        if isinstance(extensions, str):
            if len(extensions) > 0:
                extensions = [extensions]
            else:
                extensions = None  # if empty, no extension
        self.extensions: List[str] = extensions

        # === Create the menu ===
        palette: ColorPalette = replace(palette)  # copy palette
        palette.file_explorer_path = palette.explorer_prompt_path
        palette.file_explorer_dim = palette.explorer_prompt_dim
        palette.file_explorer_file = palette.explorer_prompt_file
        palette.file_explorer_directory = palette.explorer_prompt_directory
        palette.file_explorer_dots = palette.explorer_prompt_dots
        palette.file_explorer_selected = palette.explorer_prompt_selected
        palette.scrollbar = palette.explorer_prompt_scrollbar

        m = Menu(palette)

        ls = [] if len(lines) == 0 else lines.split("\n")
        h = len(ls) + items_height + 2 + 5 + 1
        w = max([items_width + 6, 30])

        rows, cols = self.height, self.width

        box = Box(rows // 2 - h // 2, cols // 2 - w // 2, h, w, palette)

        m.add(box)
        if len(title) > 0:  # add title
            m.add(
                Text(
                    title,
                    0,
                    (w - len(title)) // 2,
                    palette.text,
                    parent=box,
                    attributes=[curses.A_BOLD],
                )
            )
        for i, line in enumerate(lines.split("\n")):
            m.add(Text(line, i + 1, 2, palette.text, width=w - 4, centered=True, parent=box))

        def overwrite_prompt(path: str) -> None:
            self.confirm(
                f"File \n'{path}'\nalready exists.\nDo you want to overwrite it?",
                " OVERWRITE ",
                lambda: (self.pop_top(), try_self_call(path, save_action)),
            )

        def save_no_overwrite_prompt(path: str) -> None:
            self.confirm(
                f"Save file as\n'{path}'?",
                " SAVE ",
                lambda: (self.pop_top(), try_self_call(path, save_action)),
            )

        # == Add file explorer ==
        fe = FileExplorer(
            len(ls) + 2,
            2,
            items_height + 2,
            items_width + len(FileExplorer.file_symbol),
            False,
            file_or_dot_action=lambda s: overwrite_prompt(s),
            filter_=extensions if extensions is not None else [],
            ui=self,
            parent=box,
            palette=palette,
        )
        m.add_key_capture_drawable(fe, submenu=0)

        name_input = TextInput(h - 3, 2, width=items_width, parent=box, palette=palette)
        m.add_key_capture_drawable(name_input, submenu=0)

        def save_button_action(path: pathlib.Path) -> None:
            if len(name_input.get_text()) == 0:
                self.warning("Please enter a file name.")
                return
            else:  # if name is not empty
                filepath: pathlib.Path = path / name_input.get_text()
                if (extensions is not None) and (len(extensions) > 0):
                    if not any(str(filepath).endswith(f".{ext}") for ext in extensions):
                        filepath = filepath.with_suffix(f"{extensions[0]}")

            if os.path.isfile(filepath):  # if file exists
                overwrite_prompt(str(filepath))
            else:
                save_no_overwrite_prompt(str(filepath))

        # == Add buttons ==
        m.add_key_capture_drawable(
            Button(
                "Save",
                h - 2,
                2,
                calls(
                    lambda: try_self_call(fe.get_path(), save_button_action),
                ),
                width=w // 2 - 3,
                centered=True,
                parent=box,
            ),
            submenu=1,
        )
        m.add_key_capture_drawable(
            Button(
                "Cancel",
                h - 2,
                w // 2 + 2,
                calls(self.pop_top, self.stdscr.erase),
                width=w // 2 - 3,
                centered=True,
                parent=box,
            ),
            submenu=1,
        )

        # === activate the pop up ===
        self.add_top(m)

    def update(self) -> None:
        """Force user interface screen update."""
        self.stdscr.erase()
        self.draw(self.stdscr)
        curses.doupdate()

    def mid_update(self) -> None:
        """User interface screen update of middle strength."""
        self.draw(self.stdscr)
        curses.doupdate()

    def soft_update(self) -> None:
        """Soft user interface screen update."""
        curses.doupdate()

    def get_menu(self, name: str) -> Menu:
        """Get a menu by name."""
        return self.menus[name]
