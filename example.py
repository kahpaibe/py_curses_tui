from py_curses_tui.core import App, Menu
from py_curses_tui.genstr import GenStr

from py_curses_tui.drawables import Text, Button
from py_curses_tui.utils.colors import (
    TERMINAL_COLORS_BASIC,
    PALETTE_BASIC,
    COLOR_PAIRS_BASIC,
    Palette
)

if __name__ == "__main__":
    # ============= Application =============
    app = App(terminal_colors=TERMINAL_COLORS_BASIC, color_pairs=COLOR_PAIRS_BASIC)

    # ===== Menu 1 =====
    menu1 = Menu(palette=PALETTE_BASIC, auto_select_capturable_drawable_on_first_draw="First")
    text1 = Text(
        GenStr(("Hello, World!"[i-1], i * (-1) ** i, 0) for i in range(1, 13)),
        1,
        0,
        parent=menu1,
    )
    menu1.add_drawable(text1)

    text2 = Text(GenStr("This is a simple text element."), 1, 0, parent=text1)
    menu1.add_drawable(text2)

    button1 = Button("Click me!", 3, 0, parent=text2)
    menu1.add_drawable(button1)

    button2 = Button("Click me!", 2, 0, parent=button1, palette=Palette(3,3,4))
    menu1.add_drawable(button2)

    app.menus.append(menu1)
    app.start()
