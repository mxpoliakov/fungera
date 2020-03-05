from copy import copy
import numpy as np
from window import Window
from memory import Memory
from config import Color, MEMORY_SIZE, INSTRUCTIONS


class Queue:
    def __init__(self):
        self.organisms = []
        self.index = None

    def add_organism(self, organism):
        self.organisms.append(organism)
        if self.index is None:
            self.index = 0
            self.organisms[self.index].is_selected = True

    def get_organism(self):
        return self.organisms[self.index]

    def select_next(self):
        if self.index + 1 < len(self.organisms):
            self.organisms[self.index].is_selected = False
            self.organisms[self.index].update()
            self.index += 1
            self.organisms[self.index].is_selected = True
            self.organisms[self.index].update()

    def select_previous(self):
        if self.index - 1 >= 0:
            self.organisms[self.index].is_selected = False
            self.organisms[self.index].update()
            self.index -= 1
            self.organisms[self.index].is_selected = True
            self.organisms[self.index].update()

    def cycle_all(self):
        for organism in copy(self.organisms):
            organism.cycle()

    def update_all(self):
        for organism in copy(self.organisms):
            organism.update()


class Organism:
    def __init__(self, memory: Memory, queue: Queue, address: np.array, size: np.array):
        self.is_selected = False
        # pylint: disable=invalid-name
        self.ip = np.array(address)
        self.delta = np.array([0, 1])

        self.size = np.array(size)
        self.start = np.array(address)

        self.regs = {
            'a': np.array([0, 0]),
            'b': np.array([0, 0]),
            'c': np.array([0, 0]),
            'd': np.array([0, 0]),
        }

        self.mods = {'x': 0, 'y': 1}
        self.stack = []

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
        color = Color.SELECTED_IP if self.is_selected else Color.IP
        if (new_position >= 0).all() and (self.memory.size + new_position > 0).all():
            self.memory.window.derived(new_position, (1, 1)).background(color)

    def update(self):
        parent_color = Color.SELECTED_PARENT if self.is_selected else Color.PARENT
        self.update_window(self.size, self.start, parent_color)
        child_color = Color.SELECTED_CHILD if self.is_selected else Color.CHILD
        self.update_window(self.child_size, self.child_start, child_color)
        self.update_ip()

    def update_info(self, info_window: Window):
        info_window.print('  ip       : {}\n'.format(list(self.ip)))
        info_window.print('  delta    : {}\n'.format(list(self.delta)))
        for reg in self.regs:
            info_window.print('  r{}       : {}\n'.format(reg, list(self.regs[reg])))

        for i in range(len(self.stack)):
            info_window.print('  stack[{}] : {}\n'.format(i, list(self.stack[i])))

    def no_operation(self):
        pass

    def move_up(self):
        self.delta = np.array([-1, 0])

    def move_down(self):
        self.delta = np.array([1, 0])

    def move_right(self):
        self.delta = np.array([0, 1])

    def move_left(self):
        self.delta = np.array([0, -1])

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
        for i in range(2, max(MEMORY_SIZE)):
            if not self.memory.is_allocated(self.ip_offset(i)):
                self.child_start = self.ip_offset(i)
                self.regs[self.inst(2)] = np.copy(self.child_start)
                break
        self.child_size = np.copy(self.regs[self.inst(1)])
        self.memory.allocate(self.child_start, self.child_size)

    def load_inst(self):
        self.regs[self.inst(2)] = INSTRUCTIONS[
            self.memory.inst(self.regs[self.inst(1)])
        ][0]

    def write_inst(self):
        self.memory.write_inst(self.regs[self.inst(1)], self.regs[self.inst(2)])

    def push(self):
        self.stack.append(np.copy(self.regs[self.inst(1)]))

    def pop(self):
        self.regs[self.inst(1)] = np.copy(self.stack.pop())

    def split_child(self):
        Organism(self.memory, self.queue, self.child_start, self.child_size)
        self.child_size = np.array([0, 0])
        self.child_start = np.array([0, 0])

    def cycle(self):
        getattr(self, INSTRUCTIONS[self.inst()][1])()
        self.ip += self.delta
        self.update()
