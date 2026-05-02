from py_curses_tui.core import Application, Menu
from py_curses_tui.genstr import GenStr

from py_curses_tui.drawables import Text, Button, Box, Fill
from py_curses_tui.utils.colors import (
    TERMINAL_COLORS_BASIC,
    PALETTE_BASIC,
    COLOR_PAIRS_BASIC,
    Palette
)

if __name__ == "__main__":
    # ============= Application =============
    app = Application(terminal_colors=TERMINAL_COLORS_BASIC, color_pairs=COLOR_PAIRS_BASIC)

    # ===== Menu Test =====
    menu_test = Menu(palette=PALETTE_BASIC, default_selected="First")
    menu_text = Text(0, 0, )


    box_text = Text(2, 0)
    box = Box(2, 10, 5, 20, parent=menu_test, palette=Palette(1, 1, 1))
    menu_test.add_drawable(box)



    app.menus.append(menu_test)
    app.start()
