import numpy as np

INFO_SIZE = np.array([20, 30])
MEMORY_SIZE = np.array([1000, 1000])

SCROLL_STEP = MEMORY_SIZE // 500

KILL_ORGANISMS_RATIO = 0.5
MEMORY_FULL_RATIO = 0.75

INSTRUCTION = {
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

DELTA = {
    'LEFT': np.array([0, -1]),
    'RIGHT': np.array([0, 1]),
    'UP': np.array([-1, 0]),
    'DOWN': np.array([1, 0]),
}

COLOR = {
    'SELECTED_PARENT': 1,
    'SELECTED_CHILD': 2,
    'SELECTED_IP': 3,
    'PARENT': 4,
    'CHILD': 5,
    'IP': 6,
}
