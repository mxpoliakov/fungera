import io
import numpy as np
import modules.common as c


class Memory:
    def __init__(
        self,
        memory_map=np.full(c.config['memory_size'], '.', dtype=str),
        allocation_map=np.zeros(c.config['memory_size']),
        position=c.config['memory_size'] // 2,
    ):
        self.memory_map = memory_map
        self.allocation_map = allocation_map
        self.position = position

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
        return ratio > c.config['memory_full_ratio']

    def inst(self, address: np.array):
        return self.memory_map[tuple(address)]

    def write_inst(self, address: np.array, inst_code: np.array):
        for inst, info in c.instructions.items():
            if (info[0] == inst_code).all():
                self.memory_map[tuple(address)] = inst
                break

    def is_allocated(self, address: np.array):
        return bool(self.allocation_map[tuple(address)])

    def is_allocated_region(self, address: np.array, size: np.array):
        if (address - size < 0).any():
            return None
        if (address + size - c.config['memory_size'] > 0).any():
            return None
        allocation_region = self.allocation_map[
            address[0] : address[0] + size[0], address[1] : address[1] + size[1]
        ]
        return np.count_nonzero(allocation_region)

    def cycle(self):
        address = (
            np.random.randint(0, c.config['memory_size'][0]),
            np.random.randint(0, c.config['memory_size'][1]),
        )
        self.memory_map[address] = np.random.choice(list(c.instructions.keys()))

    def toogle(self):
        return MemoryFull(self.memory_map, self.allocation_map, self.position)

    def update(self, refresh=True):
        pass

    def clear(self):
        pass


class MemoryFull(Memory):
    def __init__(
        self,
        memory_map=np.full(c.config['memory_size'], '.', dtype=str),
        allocation_map=np.zeros(c.config['memory_size']),
        position=c.config['memory_size'] // 2,
    ):
        super(MemoryFull, self).__init__(memory_map, allocation_map, position)
        screen_display_size = c.screen.get_size()
        self.window = c.screen.derived(
            (0, c.config['info_display_size'][1]),
            (
                screen_display_size[0],
                screen_display_size[1] - c.config['info_display_size'][1],
            ),
        )
        self.size = self.window.get_size() - np.array([1, 0])
        self.update()

    def load_genome(self, genome: np.array, address: np.array, size: np.array):
        self.memory_map[
            address[0] : address[0] + size[0], address[1] : address[1] + size[1]
        ] = genome
        self.update()

    def clear(self):
        self.window.erase()
        self.window.print('', refresh=True)

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
            new_position + self.size <= c.config['memory_size']
        ).all():
            self.position += delta

        if (new_position < 0).any():
            self.position = new_position.clip(min=0)

        if new_position[0] + self.size[0] > c.config['memory_size'][0]:
            self.position[0] = c.config['memory_size'][0] - self.size[0]

        if new_position[1] + self.size[1] > c.config['memory_size'][1]:
            self.position[1] = c.config['memory_size'][1] - self.size[1]

        self.update(refresh=True)

    def write_inst(self, address: np.array, inst_code: np.array):
        super(MemoryFull, self).write_inst(address, inst_code)
        self.update(refresh=False)

    def toogle(self):
        return Memory(self.memory_map, self.allocation_map, self.position)
