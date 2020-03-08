from enum import IntEnum
import numpy as np

INFO_PANEL_SIZE = np.array([20, 40])
INITIAL_ORGANISM_POSITION = np.array([5, 25])
MEMORY_SIZE = np.array([1024, 1024])

INSTRUCTIONS = {
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
    '[': [np.array([6, 2]), 'decrement'],
    ']': [np.array([6, 3]), 'increment'],
    '-': [np.array([6, 4]), 'subtract'],
    '+': [np.array([6, 5]), 'add'],
    'L': [np.array([7, 0]), 'load_inst'],
    'W': [np.array([7, 1]), 'write_inst'],
    '@': [np.array([7, 2]), 'allocate_child'],
    '$': [np.array([7, 3]), 'split_child'],
    '{': [np.array([8, 0]), 'push'],
    '}': [np.array([8, 1]), 'pop'],
}


class Color(IntEnum):
    SELECTED_PARENT = 1
    SELECTED_CHILD = 2
    SELECTED_IP = 3
    PARENT = 4
    CHILD = 5
    IP = 6
