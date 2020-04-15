import curses
import pickle
import traceback
import numpy as np
import modules.common as c
from modules.memory import MemoryFull
from modules.queue import Queue
from modules.organism import OrganismFull


class Fungera:
    def __init__(self):
        self.queue = Queue()
        self.cycle = 0
        self.is_minimal = False
        self.info_window = c.screen.derived(
            np.array([0, 0]), c.config['info_display_size'],
        )
        self.memory = MemoryFull()
        genome_size = self.load_genome_into_memory(
            'initial.gen', c.config['memory_size'] // 2
        )
        OrganismFull(self.memory, self.queue, c.config['memory_size'] // 2, genome_size)
        self.update_info()

    def run(self):
        try:
            self.input_stream()
        except KeyboardInterrupt:
            curses.endwin()
        except Exception:
            curses.endwin()
            print(traceback.format_exc())

    def load_genome_into_memory(self, filename: str, address: np.array) -> np.array:
        with open(filename) as genome_file:
            genome = np.array([list(line.strip()) for line in genome_file])
        self.memory.load_genome(genome, address, genome.shape)
        return genome.shape

    def update_position(self, delta):
        self.memory.scroll(delta)
        self.queue.update_all()
        self.update_info()

    def update_info_full(self):
        self.info_window.erase()
        info = ''
        info += 'Cycle      : {}\n'.format(self.cycle)
        info += 'Position   : {}\n'.format(list(self.memory.position))
        info += 'Total      : {}\n'.format(len(self.queue.organisms))
        info += 'Organism   : {}\n'.format(self.queue.index)
        info += self.queue.get_organism().info()
        self.info_window.print(info)

    def update_info_minimal(self):
        self.info_window.erase()
        info = ''
        info += 'Minimal mode '
        info += '[Running]\n' if c.is_running else '[Paused]\n'
        info += 'Cycle      : {}\n'.format(self.cycle)
        info += 'Total      : {}\n'.format(len(self.queue.organisms))
        self.info_window.print(info)

    def update_info(self):
        if not self.is_minimal:
            self.update_info_full()
        else:
            if self.cycle % c.config['cycle_gap'] == 0:
                self.update_info_minimal()

    def toogle_minimal(self, memory=None):
        self.is_minimal = not self.is_minimal
        self.update_info_minimal()
        self.memory.clear()
        self.memory = self.memory.toogle() if memory is None else memory.toogle()
        self.memory.update(refresh=True)
        self.queue.toogle_minimal(self.memory)

    def save_state(self):
        return_to_full = False
        if not self.is_minimal:
            self.toogle_minimal()
            return_to_full = True
        with open(c.config['state_to_save'], 'wb') as f:
            state = {
                'cycle': self.cycle,
                'memory': self.memory,
                'queue': self.queue,
            }
            pickle.dump(state, f)
        if not self.is_minimal or return_to_full:
            self.toogle_minimal()

    def load_state(self):
        return_to_full = False
        if not self.is_minimal:
            self.toogle_minimal()
            return_to_full = True
        try:
            with open(c.config['state_to_load'], 'rb') as f:
                state = pickle.load(f)
                memory = state['memory']
                self.queue = state['queue']
                self.cycle = state['cycle']
        except Exception:
            pass
        if not self.is_minimal or return_to_full:
            self.toogle_minimal(memory)
        else:
            self.memory = memory
            self.update_info_minimal()

    def make_cycle(self):
        if c.is_running:
            if self.cycle % c.config['random_rate'] == 0:
                self.memory.cycle()
            if self.cycle % c.config['cycle_gap'] == 0:
                if self.memory.is_time_to_kill():
                    self.queue.kill_organisms()
            if not self.is_minimal:
                self.queue.update_all()
            self.cycle += 1
            self.update_info()

    def input_stream(self):
        while True:
            key = c.screen.get_key()
            if key == ord(' '):
                c.is_running = not c.is_running
                if self.is_minimal:
                    self.update_info_minimal()
            elif key == curses.KEY_DOWN and not self.is_minimal:
                self.update_position(c.config['scroll_step'] * c.deltas['down'])
            elif key == curses.KEY_UP and not self.is_minimal:
                self.update_position(c.config['scroll_step'] * c.deltas['up'])
            elif key == curses.KEY_RIGHT and not self.is_minimal:
                self.update_position(c.config['scroll_step'] * c.deltas['right'])
            elif key == curses.KEY_LEFT and not self.is_minimal:
                self.update_position(c.config['scroll_step'] * c.deltas['left'])
            elif key == ord('d') and not self.is_minimal:
                self.queue.select_next()
                self.update_info()
            elif key == ord('a') and not self.is_minimal:
                self.queue.select_previous()
                self.update_info()
            elif key == ord('m') and c.is_running:
                self.toogle_minimal()
            elif key == ord('p'):
                self.save_state()
            elif key == ord('l'):
                self.load_state()

            self.make_cycle()
            if not self.is_minimal:
                self.queue.cycle_all()
            else:
                self.queue.cycle_all_multi()


if __name__ == '__main__':
    Fungera().run()
