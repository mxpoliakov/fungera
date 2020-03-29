import numpy as np
from modules.queue import Queue
from modules.memory import Memory
from modules.common import COLOR, MEMORY_SIZE, INSTRUCTION, DELTA


class RegsDict(dict):
    def __setitem__(self, key, value):
        if key not in self:
            raise ValueError
        super().__setitem__(key, value)


class Organism:
    def __init__(self, memory: Memory, queue: Queue, address: np.array, size: np.array):
        self.is_selected = False
        # pylint: disable=invalid-name
        self.ip = np.array(address)
        self.delta = np.array([0, 1])

        self.size = np.array(size)
        self.start = np.array(address)

        self.regs = RegsDict(
            {
                'a': np.array([0, 0]),
                'b': np.array([0, 0]),
                'c': np.array([0, 0]),
                'd': np.array([0, 0]),
            }
        )

        self.mods = {'x': 0, 'y': 1}
        self.stack = []
        self.stack_len = 8
        self.errors = 0

        self.child_size = np.array([0, 0])
        self.child_start = np.array([0, 0])

        self.memory = memory
        self.memory.allocate(address, size)

        self.queue = queue
        self.queue.add_organism(self)

        self.update()

    def update_window(self, size, start, color):
        new_start = start - self.memory.position
        new_size = size + new_start.clip(max=0)
        if (new_size > 0).all() and (self.memory.size - new_start > 0).all():
            self.memory.window.derived(
                new_start.clip(min=0),
                np.minimum(new_size, self.memory.size - new_start),
            ).background(color)

    def update_ip(self):
        new_position = self.ip - self.memory.position
        color = COLOR['SELECTED_IP'] if self.is_selected else COLOR['IP']
        if (
            (new_position >= 0).all()
            and (self.memory.size - new_position > 0).all()
            and self.memory.is_allocated(self.ip)
        ):
            self.memory.window.derived(new_position, (1, 1)).background(color)

    def update(self):
        parent_color = COLOR['SELECTED_PARENT'] if self.is_selected else COLOR['PARENT']
        self.update_window(self.size, self.start, parent_color)
        child_color = COLOR['SELECTED_CHILD'] if self.is_selected else COLOR['CHILD']
        self.update_window(self.child_size, self.child_start, child_color)
        self.update_ip()

    def info(self):
        info = ''
        info += '  errors   : {}\n'.format(self.errors)
        info += '  ip       : {}\n'.format(list(self.ip))
        info += '  delta    : {}\n'.format(list(self.delta))
        for reg in self.regs:
            info += '  r{}       : {}\n'.format(reg, list(self.regs[reg]))
        for i in range(len(self.stack)):
            info += '  stack[{}] : {}\n'.format(i, list(self.stack[i]))
        for i in range(len(self.stack), self.stack_len):
            info += '  stack[{}] : \n'.format(i)
        return info

    def no_operation(self):
        pass

    def move_up(self):
        self.delta = DELTA['UP']

    def move_down(self):
        self.delta = DELTA['DOWN']

    def move_right(self):
        self.delta = DELTA['RIGHT']

    def move_left(self):
        self.delta = DELTA['LEFT']

    def ip_offset(self, offset: int = 0) -> np.array:
        return self.ip + offset * self.delta

    def inst(self, offset: int = 0) -> str:
        return self.memory.inst(self.ip_offset(offset))

    def find_template(self):
        register = self.inst(1)
        template = []
        for i in range(2, max(self.size)):
            if self.inst(i) in ['.', ':']:
                template.append(':' if self.inst(i) == '.' else '.')
            else:
                break
        counter = 0
        for i in range(i, max(self.size)):
            if self.inst(i) == template[counter]:
                counter += 1
            else:
                counter = 0
            if counter == len(template):
                self.regs[register] = self.ip + i * self.delta
                break

    def if_not_zero(self):
        if self.inst(1) in self.mods.keys():
            value = self.regs[self.inst(2)][self.mods[self.inst(1)]]
            start_from = 1
        else:
            value = self.regs[self.inst(1)]
            start_from = 0

        if not np.any(value):
            self.ip = self.ip_offset(start_from + 1)
        else:
            self.ip = self.ip_offset(start_from + 2)

    def increment(self):
        if self.inst(1) in self.mods.keys():
            self.regs[self.inst(2)][self.mods[self.inst(1)]] += 1
        else:
            self.regs[self.inst(1)] += 1

    def decrement(self):
        if self.inst(1) in self.mods.keys():
            self.regs[self.inst(2)][self.mods[self.inst(1)]] -= 1
        else:
            self.regs[self.inst(1)] -= 1

    def zero(self):
        self.regs[self.inst(1)] = np.array([0, 0])

    def one(self):
        self.regs[self.inst(1)] = np.array([1, 1])

    def subtract(self):
        self.regs[self.inst(3)] = self.regs[self.inst(1)] - self.regs[self.inst(2)]

    def allocate_child(self):
        size = np.copy(self.regs[self.inst(1)])
        is_space_found = False
        for i in range(2, max(MEMORY_SIZE)):
            is_allocated_region = self.memory.is_allocated_region(
                self.ip_offset(i), size
            )
            if is_allocated_region is None:
                break
            if not is_allocated_region:
                self.child_start = self.ip_offset(i)
                self.regs[self.inst(2)] = np.copy(self.child_start)
                is_space_found = True
                break
        if is_space_found:
            self.child_size = np.copy(self.regs[self.inst(1)])
            self.memory.allocate(self.child_start, self.child_size)

    def load_inst(self):
        self.regs[self.inst(2)] = INSTRUCTION[
            self.memory.inst(self.regs[self.inst(1)])
        ][0]

    def write_inst(self):
        if not np.array_equal(self.child_size, np.array([0, 0])):
            self.memory.write_inst(self.regs[self.inst(1)], self.regs[self.inst(2)])

    def push(self):
        if len(self.stack) < self.stack_len:
            self.stack.append(np.copy(self.regs[self.inst(1)]))

    def pop(self):
        self.regs[self.inst(1)] = np.copy(self.stack.pop())

    def split_child(self):
        if not np.array_equal(self.child_size, np.array([0, 0])):
            self.memory.deallocate(self.child_start, self.child_size)
            Organism(self.memory, self.queue, self.child_start, self.child_size)
        self.child_size = np.array([0, 0])
        self.child_start = np.array([0, 0])

    def __lt__(self, other):
        return self.errors < other.errors

    def kill(self):
        self.memory.deallocate(self.start, self.size)
        self.size = np.array([0, 0])
        if not np.array_equal(self.child_size, np.array([0, 0])):
            self.memory.deallocate(self.child_start, self.child_size)
        self.child_size = np.array([0, 0])
        self.update()
        self.memory.update(refresh=True)

    def cycle(self):
        try:
            getattr(self, INSTRUCTION[self.inst()][1])()
        except Exception:
            self.errors += 1
        new_ip = self.ip + self.delta
        if (new_ip < 0).any() or (new_ip - MEMORY_SIZE > 0).any():
            self.update()
        else:
            self.ip = np.copy(new_ip)
            self.update()
