import curses

from py_curses_tui.core import Application, Menu
from py_curses_tui.genstr import GenStr

from py_curses_tui.drawables import Text, Button, Box, Fill, Choose, TextDynamic
from py_curses_tui.utils.colors import (
    TERMINAL_COLORS_BASIC,
    PALETTE_BASIC,
    COLOR_PAIRS_BASIC,
    Palette,
)


if __name__ == "__main__":
    # ============= Application =============
    app = Application(
        terminal_colors=TERMINAL_COLORS_BASIC, color_pairs=COLOR_PAIRS_BASIC
    )

    W, H = 60, 20

    # ===== Menu Test =====
    menu_test = Menu(palette=PALETTE_BASIC, default_selected="First")

    menu_text_border = Box(0, 0, 3, W, parent=menu_test, palette=Palette(1, 1, 1))
    menu_test.add_drawable(menu_text_border)
    menu_text = Text(GenStr("Drawable test menu"), 1, 1, W - 2, True, parent=menu_test)
    menu_test.add_drawable(menu_text)

    box_text = Text(GenStr(("Box", None, [curses.A_BOLD])), 4, 0, parent=menu_test)
    menu_test.add_drawable(box_text)
    box = Box(1, 0, 4, 15, parent=box_text, palette=Palette(-2, 1, 1))
    menu_test.add_drawable(box)

    fill_text = Text(GenStr(("Fill", None, [curses.A_BOLD])), 4, 17, parent=menu_test)
    menu_test.add_drawable(fill_text)
    fill = Fill(1, 0, 4, 15, parent=fill_text, palette=Palette(-11, 1, 1))
    menu_test.add_drawable(fill)

    text_text = Text(GenStr(("Text", None, [curses.A_BOLD])), 4, 34, parent=menu_test)
    menu_test.add_drawable(text_text)
    text = Text(
        GenStr(
            ("This is a text drawable."[i], ((i % 7) + 1) * (-1) ** (i // 8))
            for i in range(24)
        ),
        1,
        0,
        parent=text_text,
        palette=Palette(-2, 1, 1),
    )
    menu_test.add_drawable(text)

    button_text = Text(
        GenStr(("Button", None, [curses.A_BOLD])), 10, 0, parent=menu_test
    )
    menu_test.add_drawable(button_text)
    button = Button(
        "Click me",
        1,
        0,
        action=lambda button: print("Button clicked!"),
        parent=button_text,
        palette=Palette(-11, 1, 1),
    )
    menu_test.add_drawable(button)

    choose_text = Text(
        GenStr(("Choose", None, [curses.A_BOLD])), 10, 17, parent=menu_test
    )
    menu_test.add_drawable(choose_text)
    choose = Choose(
        1,
        0,
        options=[
            ("Option 1", lambda choose: print("Option 1 selected!")),
            ("Option 2", lambda choose: print("Option 2 selected!")),
            ("Option 3", lambda choose: choose.options.append(("New Option", lambda choose: print("New Option selected!")))),
        ],
        parent=choose_text,
        palette=Palette(-11, 1, 1),
    )
    menu_test.add_drawable(choose)

    def _dyna_text(td: TextDynamic) -> GenStr:
        out_str = f"Dynamic text: {app.menus[0]._selected_drawable_index:}"

        

        return GenStr((out_str, -12))
    
    dyna_text = TextDynamic(text_getter=_dyna_text, y=10, x=34, parent=menu_test)
    menu_test.add_drawable(dyna_text)

    app.menus.append(menu_test)
    app.start()
