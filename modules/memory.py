import io
import numpy as np
from modules.window import Window
from modules.common import MEMORY_SIZE, INFO_SIZE, INSTRUCTION, MEMORY_FULL_RATIO


class Memory:
    def __init__(self, screen: Window):
        self.memory_map = np.full(MEMORY_SIZE, '.', dtype=str)
        self.allocation_map = np.zeros(MEMORY_SIZE)
        screen_display_size = screen.get_size()
        self.window = screen.derived(
            (0, INFO_SIZE[1]),
            (screen_display_size[0], screen_display_size[1] - INFO_SIZE[1]),
        )
        self.size = self.window.get_size() - np.array([1, 0])
        self.position = MEMORY_SIZE // 2
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

    def deallocate(self, address: np.array, size: np.array):
        try:
            self.allocation_map[
                address[0] : address[0] + size[0], address[1] : address[1] + size[1]
            ] = np.zeros(size)
        except Exception:
            pass

    def is_time_to_kill(self):
        ratio = np.count_nonzero(self.allocation_map) / np.count_nonzero(
            self.allocation_map == 0
        )
        return ratio > MEMORY_FULL_RATIO

    def update(self, refresh=False):
        buffer = io.BytesIO()
        memory_map_subset = self.memory_map[
            self.position[0] : self.size[0] + self.position[0],
            self.position[1] : self.size[1] + self.position[1],
        ]
        np.savetxt(
            buffer, memory_map_subset, fmt='%s', delimiter='', newline='',
        )
        self.window.erase()
        self.window.print(buffer.getvalue(), refresh=refresh)

    def scroll(self, delta: np.array):
        new_position = self.position + delta
        if (new_position >= 0).all() and (
            new_position + self.size <= MEMORY_SIZE
        ).all():
            self.position += delta

        if (new_position < 0).any():
            self.position = new_position.clip(min=0)

        if new_position[0] + self.size[0] > MEMORY_SIZE[0]:
            self.position[0] = MEMORY_SIZE[0] - self.size[0]

        if new_position[1] + self.size[1] > MEMORY_SIZE[1]:
            self.position[1] = MEMORY_SIZE[1] - self.size[1]

        self.update(refresh=True)

    def inst(self, address: np.array):
        return self.memory_map[tuple(address)]

    def write_inst(self, address: np.array, inst_code: np.array):
        for inst, info in INSTRUCTION.items():
            if (info[0] == inst_code).all():
                self.memory_map[tuple(address)] = inst
                self.update(refresh=False)
                break

    def is_allocated(self, address: np.array):
        return bool(self.allocation_map[tuple(address)])

    def is_allocated_region(self, address: np.array, size: np.array):
        if (address - size < 0).any():
            return None
        if (address + size - MEMORY_SIZE > 0).any():
            return None
        allocation_region = self.allocation_map[
            address[0] : address[0] + size[0], address[1] : address[1] + size[1]
        ]
        return np.count_nonzero(allocation_region)

    def cycle(self):
        address = (
            np.random.randint(0, MEMORY_SIZE[0]),
            np.random.randint(0, MEMORY_SIZE[1]),
        )
        self.memory_map[address] = np.random.choice(list(INSTRUCTION.keys()))
