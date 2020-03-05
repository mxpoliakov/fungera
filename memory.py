import io
import numpy as np
from window import Window
from config import MEMORY_SIZE, INFO_PANEL_SIZE, INSTRUCTIONS


class Memory:
    def __init__(self, screen: Window):
        self.memory_map = np.full(MEMORY_SIZE, '.', dtype=str)
        self.allocation_map = np.zeros(MEMORY_SIZE)
        screen_display_size = screen.get_size()
        self.window = screen.derived(
            (0, INFO_PANEL_SIZE[1]),
            (screen_display_size[0], screen_display_size[1] - INFO_PANEL_SIZE[1]),
        )
        self.size = self.window.get_size() - np.array([1, 0])
        self.position = np.array([0, 0])
        self.update()

    def load_genome(self, genome: np.array, address: np.array, size: np.array):
        self.memory_map[
            address[0] : address[0] + size[0], address[1] : address[1] + size[1]
        ] = genome
        self.update()

    def allocate(self, address: np.array, size: np.array):
        self.allocation_map[
            address[0] : address[0] + size[0], address[1] : address[1] + size[1]
        ] = np.ones(size)

    def update(self):
        buffer = io.BytesIO()
        memory_map_subset = self.memory_map[
            self.position[0] : self.size[0] + self.position[0],
            self.position[1] : self.size[1] + self.position[1],
        ]
        np.savetxt(
            buffer, memory_map_subset, fmt='%s', delimiter='', newline='',
        )
        self.window.erase()
        self.window.print(buffer.getvalue())

    def scroll(self, delta: np.array):
        new_position = self.position + delta
        if (new_position >= 0).all():
            self.position += delta
            self.update()

    def inst(self, address: np.array):
        return self.memory_map[tuple(address)]

    def write_inst(self, address: np.array, inst_code: np.array):
        for inst, info in INSTRUCTIONS.items():
            if (info[0] == inst_code).all():
                self.memory_map[tuple(address)] = inst
                self.update()
                break

    def is_allocated(self, address: np.array):
        return bool(self.allocation_map[tuple(address)])
