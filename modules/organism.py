import uuid
from typing import Optional
import numpy as np
import modules.common as c
import modules.memory as m
import modules.queue as q


class RegsDict(dict):
    allowed_keys = ['a', 'b', 'c', 'd']

    def __setitem__(self, key, value):
        if key not in self.allowed_keys:
            raise ValueError
        super().__setitem__(key, value)


class Organism:
    def __init__(
        self,
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
        children: Optional[int] = 0,
        reproduction_cycle: Optional[int] = 0,
        parent: Optional[uuid.UUID] = None,
    ):
        # pylint: disable=invalid-name
        self.id = uuid.uuid4()
        self.parent = parent
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

        if address is not None:
            m.memory.allocate(address, size)

        self.reproduction_cycle = reproduction_cycle
        self.children = children

        q.queue.add_organism(self)
        q.queue.archive.append(self)

        self.mods = {'x': 0, 'y': 1}

    def no_operation(self):
        pass

    def move_up(self):
        self.delta = c.deltas['up']

    def move_down(self):
        self.delta = c.deltas['down']

    def move_right(self):
        self.delta = c.deltas['right']

    def move_left(self):
        self.delta = c.deltas['left']

    def ip_offset(self, offset: int = 0) -> np.array:
        return self.ip + offset * self.delta

    def inst(self, offset: int = 0) -> str:
        return m.memory.inst(self.ip_offset(offset))

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
        if (size <= 0).any():
            return
        is_space_found = False
        for i in range(2, max(c.config['memory_size'])):
            is_allocated_region = m.memory.is_allocated_region(self.ip_offset(i), size)
            if is_allocated_region is None:
                break
            if not is_allocated_region:
                self.child_start = self.ip_offset(i)
                self.regs[self.inst(2)] = np.copy(self.child_start)
                is_space_found = True
                break
        if is_space_found:
            self.child_size = np.copy(self.regs[self.inst(1)])
            m.memory.allocate(self.child_start, self.child_size)

    def load_inst(self):
        self.regs[self.inst(2)] = c.instructions[
            m.memory.inst(self.regs[self.inst(1)])
        ][0]

    def write_inst(self):
        if not np.array_equal(self.child_size, np.array([0, 0])):
            m.memory.write_inst(self.regs[self.inst(1)], self.regs[self.inst(2)])

    def push(self):
        if len(self.stack) < c.config['stack_length']:
            self.stack.append(np.copy(self.regs[self.inst(1)]))

    def pop(self):
        self.regs[self.inst(1)] = np.copy(self.stack.pop())

    def split_child(self):
        if not np.array_equal(self.child_size, np.array([0, 0])):
            m.memory.deallocate(self.child_start, self.child_size)
            self.__class__(self.child_start, self.child_size, parent=self.id)
            self.children += 1
            self.reproduction_cycle = 0
        self.child_size = np.array([0, 0])
        self.child_start = np.array([0, 0])

    def __lt__(self, other):
        return self.errors < other.errors

    def kill(self):
        m.memory.deallocate(self.start, self.size)
        self.size = np.array([0, 0])
        if not np.array_equal(self.child_size, np.array([0, 0])):
            m.memory.deallocate(self.child_start, self.child_size)
        self.child_size = np.array([0, 0])

    def cycle(self):
        try:
            getattr(self, c.instructions[self.inst()][1])()
        except Exception:
            self.errors += 1
        new_ip = self.ip + self.delta
        self.reproduction_cycle += 1
        if (
            self.errors > c.config['organism_death_rate']
            or self.reproduction_cycle > c.config['kill_if_no_child']
        ):
            q.queue.organisms.remove(self)
            self.kill()
        if (new_ip < 0).any() or (new_ip - c.config['memory_size'] > 0).any():
            return None
        self.ip = np.copy(new_ip)
        return None

    def update(self):
        pass

    def toogle(self):
        OrganismFull(
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
            children=self.children,
            reproduction_cycle=self.reproduction_cycle,
            parent=self.parent,
        )


class OrganismFull(Organism):
    def __init__(
        self,
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
        children: Optional[int] = 0,
        reproduction_cycle: Optional[int] = 0,
        parent: Optional[uuid.UUID] = None,
    ):
        super(OrganismFull, self).__init__(
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
            children=children,
            reproduction_cycle=reproduction_cycle,
            parent=parent,
        )

        self.update()

    def update_window(self, size, start, color):
        new_start = start - m.memory.position
        new_size = size + new_start.clip(max=0)
        if (new_size > 0).all() and (m.memory.size - new_start > 0).all():
            m.memory.window.derived(
                new_start.clip(min=0),
                np.amin([new_size, m.memory.size - new_start, m.memory.size], axis=0),
            ).background(color)

    def update_ip(self):
        new_position = self.ip - m.memory.position
        color = c.colors['ip_bold'] if self.is_selected else c.colors['ip']
        if (
            (new_position >= 0).all()
            and (m.memory.size - new_position > 0).all()
            and m.memory.is_allocated(self.ip)
        ):
            m.memory.window.derived(new_position, (1, 1)).background(color)

    def update(self):
        parent_color = (
            c.colors['parent_bold'] if self.is_selected else c.colors['parent']
        )
        self.update_window(self.size, self.start, parent_color)
        child_color = c.colors['child_bold'] if self.is_selected else c.colors['child']
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
        for i in range(len(self.stack), c.config['stack_length']):
            info += '  stack[{}] : \n'.format(i)
        return info

    def kill(self):
        super(OrganismFull, self).kill()
        self.update()
        m.memory.update(refresh=True)

    def toogle(self):
        Organism(
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
            children=self.children,
            reproduction_cycle=self.reproduction_cycle,
            parent=self.parent,
        )
