from py_curses_tui.core import Application, Menu
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
    app = Application(terminal_colors=TERMINAL_COLORS_BASIC, color_pairs=COLOR_PAIRS_BASIC)

    # ===== Menu 1 =====
    menu1 = Menu(palette=PALETTE_BASIC, default_selected="First")
    text1 = Text(
        GenStr(("Hello, World!"[i-1], i * (-1) ** i) for i in range(1, 13)),
        1,
        0,
        parent=menu1,
    )
    menu1.add_drawable(text1)

    text2 = Text(GenStr("This is a simple text element."), 1, 0, parent=text1)
    menu1.add_drawable(text2)

    def _action(button: Button) -> None:
        button.width = 1 if not button.width else button.width + 1

    button1 = Button("Click me!", 3, 0, _action, parent=text2)
    menu1.add_drawable(button1)

    button2 = Button("Click me!", 2, 0, _action, parent=button1, palette=Palette(3,3,4))
    menu1.add_drawable(button2)

    button3 = Button("Click me!", 1, 0, _action, parent=button2, palette=Palette(4,4,3))
    menu1.add_drawable(button3)

    app.menus.append(menu1)
    app.start()
