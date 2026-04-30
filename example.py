from py_curses_tui.core import App, Menu
from py_curses_tui.genstr import GenStr

from py_curses_tui.drawables import Text, Button

if __name__ == '__main__':
    # ============= Application =============
    app = App()

    # ===== Menu 1 =====
    menu1 = Menu(auto_select_capturable_drawable_on_first_draw="First")
    text1 = Text(GenStr("Hello, World!"), 1, 0, parent=menu1)
    menu1.add_drawable(text1)

    text2 = Text(GenStr("This is a simple text element."), 1, 0, parent=menu1)
    menu1.add_drawable(text2)

    button1 = Button("Click me!", 3, 0, parent=text2)
    menu1.add_drawable(button1)

    button2 = Button("Click me!", 2, 0, parent=button1)
    menu1.add_drawable(button2)

    app.menus.append(menu1)
    app.start()