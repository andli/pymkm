#!/usr/bin/env python3
"""
A very lightweight console menu.
"""

__author__ = "Andreas Ehrlund"
__version__ = "0.9.0"
__license__ = "MIT"

import sys

PADDING = 6

class MicroMenu:


    def __init__(self, menu_title):
        self.PADDING = 6
        self.menu_title = menu_title
        self.menu_items = []

    def add_function_item(self, title, func_ref, kwargs):
        self.menu_items.append((title, func_ref, kwargs))
    
    def show(self):
        while True:
            self.print_menu(self.menu_title, self.menu_items)
            choice = int(input("Action number: "))

            if 0 == choice:
                break
            elif choice in range(len(self.menu_items) + 1):
                func = self.menu_items[choice - 1][1]
                kwargs = self.menu_items[choice - 1][2]
                func(**kwargs)
        
    def print_menu(self, title, menu_items):
        menu_width = self.PADDING + max(len(item[0]) for item in menu_items)
        menu_top_left = 3 * "─"
        menu_top_right = (menu_width - len(title) - 1) * "─" + "╮"
        menu_top = f"╭{menu_top_left} {title} {menu_top_right}"
        print(menu_top)

        index = 1
        for item in menu_items:
            print("│ {}: {}{}│".format(
                str(index),
                item[0],
                (menu_width - len(item[0])) * " "
            ))
            index += 1
        print("│ 0: Exit" + (len(menu_top) - 10) * " " + "│")
        print("╰" + (len(menu_top) - 2) * "─" + "╯")
