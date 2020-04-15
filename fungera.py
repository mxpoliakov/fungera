import curses
import pickle
import traceback
import numpy as np
from modules.memory import MemoryFull
from modules.queue import Queue
from modules.organism import OrganismFull
from modules.common import screen, config, deltas


class Fungera:
    def __init__(self):
        self.queue = Queue()
        self.cycle = 0
        self.running = False
        self.minimal = False
        self.info_window = screen.derived(
            np.array([0, 0]), config['info_display_size'],
        )
        self.memory = MemoryFull()
        genome_size = self.load_genome_into_memory(
            'initial.gen', config['memory_size'] // 2
        )
        OrganismFull(self.memory, self.queue, config['memory_size'] // 2, genome_size)
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
        info += '[Running]\n' if self.running else '[Paused]\n'
        info += 'Cycle      : {}\n'.format(self.cycle)
        info += 'Total      : {}\n'.format(len(self.queue.organisms))
        self.info_window.print(info)

    def update_info(self):
        if not self.minimal:
            self.update_info_full()
        else:
            if self.cycle % config['cycle_gap'] == 0:
                self.update_info_minimal()

    def toogle_minimal(self, memory=None):
        self.minimal = not self.minimal
        self.update_info_minimal()
        self.memory.clear()
        self.memory = self.memory.toogle() if memory is None else memory.toogle()
        self.memory.update(refresh=True)
        self.queue.toogle_minimal(self.memory)

    def save_state(self):
        return_to_full = False
        if not self.minimal:
            self.toogle_minimal()
            return_to_full = True
        with open(config['state_to_save'], 'wb') as f:
            state = {
                'cycle': self.cycle,
                'memory': self.memory,
                'queue': self.queue,
            }
            pickle.dump(state, f)
        if not self.minimal or return_to_full:
            self.toogle_minimal()

    def load_state(self):
        return_to_full = False
        if not self.minimal:
            self.toogle_minimal()
            return_to_full = True
        try:
            with open(config['state_to_load'], 'rb') as f:
                state = pickle.load(f)
                memory = state['memory']
                self.queue = state['queue']
                self.cycle = state['cycle']
        except Exception:
            pass
        if not self.minimal or return_to_full:
            self.toogle_minimal(memory)
        else:
            self.memory = memory
            self.update_info_minimal()

    def make_cycle(self):
        if self.cycle % config['random_rate'] == 0:
            self.memory.cycle()
        if self.cycle % config['cycle_gap'] == 0:
            if self.memory.is_time_to_kill():
                self.queue.kill_organisms()
        self.queue.cycle_all()
        if not self.minimal:
            self.queue.update_all()
        self.cycle += 1
        self.update_info()

    def input_stream(self):
        while True:
            key = screen.get_key()
            if key == -1 and self.running:
                self.make_cycle()
            elif key == ord('c') and not self.running:
                self.make_cycle()
            elif key == ord(' '):
                self.running = not self.running
                if self.minimal:
                    self.update_info_minimal()
            elif key == curses.KEY_DOWN and not self.minimal:
                self.update_position(config['scroll_step'] * deltas['down'])
            elif key == curses.KEY_UP and not self.minimal:
                self.update_position(config['scroll_step'] * deltas['up'])
            elif key == curses.KEY_RIGHT and not self.minimal:
                self.update_position(config['scroll_step'] * deltas['right'])
            elif key == curses.KEY_LEFT and not self.minimal:
                self.update_position(config['scroll_step'] * deltas['left'])
            elif key == ord('d') and not self.minimal:
                self.queue.select_next()
                self.update_info()
            elif key == ord('a') and not self.minimal:
                self.queue.select_previous()
                self.update_info()
            elif key == ord('m') and self.running:
                self.toogle_minimal()
            elif key == ord('p') and self.running:
                self.save_state()
            elif key == ord('l') and self.running:
                self.load_state()


if __name__ == '__main__':
    Fungera().run()
