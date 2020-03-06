from __future__ import annotations
import curses
import numpy as np


class Window:
    def __init__(self, window):
        self.window = window

    def derived(self, address: np.array, size: np.array) -> Window:
        return Window(self.window.derwin(size[0], size[1], address[0], address[1]))

    def get_size(self) -> np.array:
        return np.array(self.window.getmaxyx())

    def erase(self):
        self.window.erase()

    def get_key(self):
        return self.window.getch()

    def print(self, string: str):
        self.window.addstr(string)
        self.window.refresh()

    def background(self, color: int):
        self.window.bkgd(' ', curses.color_pair(color))
        self.window.refresh()

    def setup(self):
        self.window.clear()
        self.window.nodelay(1)
        self.window.keypad(True)
