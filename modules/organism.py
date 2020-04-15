from typing import Optional
import numpy as np
from modules.queue import Queue
from modules.memory import Memory
from modules.common import config, colors, instructions, deltas


class RegsDict(dict):
    allowed_keys = ['a', 'b', 'c', 'd']

    def __setitem__(self, key, value):
        if key not in self.allowed_keys:
            raise ValueError
        super().__setitem__(key, value)


class Organism:
    def __init__(
        self,
        memory: Memory,
        queue: Queue,
        address: np.array,
        size: np.array,
        ip: Optional[np.array] = None,
        delta: Optional[np.array] = np.array([0, 1]),
        start: Optional[np.array] = None,
        regs: Optional[RegsDict] = None,
        stack: Optional[list] = None,
        errors: Optional[int] = 0,
        child_size: Optional[np.array] = np.array([0, 0]),
        child_start: Optional[np.array] = np.array([0, 0]),
        is_selected: Optional[bool] = False,
    ):
        # pylint: disable=invalid-name
        self.ip = np.array(address) if ip is None and address is not None else ip
        self.delta = delta

        self.size = np.array(size)
        self.start = (
            np.array(address) if start is None and address is not None else start
        )
        self.regs = (
            RegsDict(
                {
                    'a': np.array([0, 0]),
                    'b': np.array([0, 0]),
                    'c': np.array([0, 0]),
                    'd': np.array([0, 0]),
                }
            )
            if regs is None
            else regs
        )
        self.stack = [] if stack is None else stack

        self.errors = errors

        self.child_size = child_size
        self.child_start = child_start

        self.is_selected = is_selected

        self.memory = memory
        if address is not None:
            self.memory.allocate(address, size)

        self.queue = queue
        self.queue.add_organism(self)

        self.mods = {'x': 0, 'y': 1}

    def no_operation(self):
        pass

    def move_up(self):
        self.delta = deltas['up']

    def move_down(self):
        self.delta = deltas['down']

    def move_right(self):
        self.delta = deltas['right']

    def move_left(self):
        self.delta = deltas['left']

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
        for i in range(2, max(config['memory_size'])):
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
        self.regs[self.inst(2)] = instructions[
            self.memory.inst(self.regs[self.inst(1)])
        ][0]

    def write_inst(self):
        if not np.array_equal(self.child_size, np.array([0, 0])):
            self.memory.write_inst(self.regs[self.inst(1)], self.regs[self.inst(2)])

    def push(self):
        if len(self.stack) < config['stack_length']:
            self.stack.append(np.copy(self.regs[self.inst(1)]))

    def pop(self):
        self.regs[self.inst(1)] = np.copy(self.stack.pop())

    def split_child(self):
        if not np.array_equal(self.child_size, np.array([0, 0])):
            self.memory.deallocate(self.child_start, self.child_size)
            self.__class__(self.memory, self.queue, self.child_start, self.child_size)
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

    def cycle(self):
        try:
            getattr(self, instructions[self.inst()][1])()
        except Exception:
            self.errors += 1
        new_ip = self.ip + self.delta
        if (new_ip < 0).any() or (new_ip - config['memory_size'] > 0).any():
            return None
        self.ip = np.copy(new_ip)
        return None

    def toogle(self, memory):
        OrganismFull(
            memory=memory,
            queue=self.queue,
            address=None,
            size=self.size,
            ip=self.ip,
            delta=self.delta,
            start=self.start,
            regs=self.regs,
            stack=self.stack,
            errors=self.errors,
            child_size=self.child_size,
            child_start=self.child_start,
            is_selected=self.is_selected,
        )


class OrganismFull(Organism):
    def __init__(
        self,
        memory: Memory,
        queue: Queue,
        address: np.array,
        size: np.array,
        ip: Optional[np.array] = None,
        delta: Optional[np.array] = np.array([0, 1]),
        start: Optional[np.array] = None,
        regs: Optional[RegsDict] = None,
        stack: Optional[list] = None,
        errors: Optional[int] = 0,
        child_size: Optional[np.array] = np.array([0, 0]),
        child_start: Optional[np.array] = np.array([0, 0]),
        is_selected: Optional[bool] = False,
    ):
        super(OrganismFull, self).__init__(
            memory=memory,
            queue=queue,
            address=address,
            size=size,
            ip=ip,
            delta=delta,
            start=start,
            regs=regs,
            stack=stack,
            errors=errors,
            child_size=child_size,
            child_start=child_start,
            is_selected=is_selected,
        )

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
        color = colors['ip_bold'] if self.is_selected else colors['ip_bold']
        if (
            (new_position >= 0).all()
            and (self.memory.size - new_position > 0).all()
            and self.memory.is_allocated(self.ip)
        ):
            self.memory.window.derived(new_position, (1, 1)).background(color)

    def update(self):
        parent_color = colors['parent_bold'] if self.is_selected else colors['parent']
        self.update_window(self.size, self.start, parent_color)
        child_color = colors['child_bold'] if self.is_selected else colors['child']
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
        for i in range(len(self.stack), config['stack_length']):
            info += '  stack[{}] : \n'.format(i)
        return info

    def kill(self):
        super(OrganismFull, self).kill()
        self.update()
        self.memory.update(refresh=True)

    def toogle(self, memory):
        Organism(
            memory=memory,
            queue=self.queue,
            address=None,
            size=self.size,
            ip=self.ip,
            delta=self.delta,
            start=self.start,
            regs=self.regs,
            stack=self.stack,
            errors=self.errors,
            child_size=self.child_size,
            child_start=self.child_start,
            is_selected=self.is_selected,
        )
