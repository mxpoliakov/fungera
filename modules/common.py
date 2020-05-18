import curses
import os
import argparse
from threading import Thread, Event
import toml
import numpy as np
import modules.window as w


class RepeatedTimer(Thread):
    def __init__(self, interval, function, args=None, kwargs=None):
        Thread.__init__(self)
        self.interval = interval
        self.function = function
        self.args = args if args is not None else []
        self.kwargs = kwargs if kwargs is not None else {}
        self.finished = Event()
        self.start()

    def cancel(self):
        self.finished.set()

    def run(self):
        while not self.finished.wait(self.interval[0]):
            if not self.finished.is_set():
                self.function(*self.args, **self.kwargs)
                self.interval[0] *= self.interval[1]
        self.finished.set()


instructions = {
    '.': [np.array([0, 0]), 'no_operation'],
    ':': [np.array([0, 1]), 'no_operation'],
    'a': [np.array([1, 0]), 'no_operation'],
    'b': [np.array([1, 1]), 'no_operation'],
    'c': [np.array([1, 2]), 'no_operation'],
    'd': [np.array([1, 3]), 'no_operation'],
    'x': [np.array([2, 0]), 'no_operation'],
    'y': [np.array([2, 1]), 'no_operation'],
    '^': [np.array([3, 0]), 'move_up'],
    'v': [np.array([3, 1]), 'move_down'],
    '>': [np.array([3, 2]), 'move_right'],
    '<': [np.array([3, 3]), 'move_left'],
    '&': [np.array([4, 0]), 'find_template'],
    '?': [np.array([5, 0]), 'if_not_zero'],
    '1': [np.array([6, 0]), 'one'],
    '0': [np.array([6, 1]), 'zero'],
    '-': [np.array([6, 2]), 'decrement'],
    '+': [np.array([6, 3]), 'increment'],
    '~': [np.array([6, 4]), 'subtract'],
    'L': [np.array([7, 0]), 'load_inst'],
    'W': [np.array([7, 1]), 'write_inst'],
    '@': [np.array([7, 2]), 'allocate_child'],
    '$': [np.array([7, 3]), 'split_child'],
    'S': [np.array([8, 0]), 'push'],
    'P': [np.array([8, 1]), 'pop'],
}

deltas = {
    'left': np.array([0, -1]),
    'right': np.array([0, 1]),
    'up': np.array([-1, 0]),
    'down': np.array([1, 0]),
}

colors = {
    'parent_bold': 1,
    'child_bold': 2,
    'ip_bold': 3,
    'parent': 4,
    'child': 5,
    'ip': 6,
}


def init_curses():
    terminal_size = os.get_terminal_size()
    if terminal_size.columns < 100 or terminal_size.lines < 25:
        print(
            'Terminal size is too small. The terminal size must be at least (100, 25)'
        )
        print(
            'Your terminal size: ({}, {})'.format(
                terminal_size.columns, terminal_size.lines
            )
        )
        exit(0)
    _screen = w.Window(curses.initscr())
    _screen.setup()

    curses.noecho()
    curses.cbreak()
    curses.curs_set(0)

    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(colors['parent_bold'], curses.COLOR_WHITE, 126)
    curses.init_pair(colors['ip_bold'], curses.COLOR_WHITE, 160)
    curses.init_pair(colors['child_bold'], curses.COLOR_WHITE, 128)
    curses.init_pair(colors['parent'], curses.COLOR_WHITE, 27)
    curses.init_pair(colors['ip'], curses.COLOR_WHITE, 117)
    curses.init_pair(colors['child'], curses.COLOR_WHITE, 33)
    return _screen


def load_config():
    _config = {}
    for key, value in toml.load('config.toml').items():
        _config[key] = np.array(value) if isinstance(value, list) else value
    _config['simulation_name'] = line_args.name
    _config['snapshot_to_load'] = line_args.state
    return _config


is_running = False

parser = argparse.ArgumentParser(
    description='Fungera - two-dimentional artificial life simulator'
)
parser.add_argument('--name', default='Simulation 1', help='Simulation name')
parser.add_argument(
    '--state', default='new', help='State file to load (new/last/filename)'
)

line_args = parser.parse_args()

try:
    screen = init_curses()
except Exception:
    print('No display found')
    screen = None

config = load_config()
