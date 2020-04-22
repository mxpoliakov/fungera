import curses
import pickle
import traceback
import glob
import os
import numpy as np
import modules.common as c
import modules.memory as m
import modules.queue as q
import modules.organism as o


class Fungera:
    def __init__(self):
        self.timer = c.RepeatedTimer(c.config['autosave_rate'], self.save_state)
        np.random.seed(c.config['random_seed'])
        if not os.path.exists('snapshots'):
            os.makedirs('snapshots')
        self.cycle = 0
        self.is_minimal = False
        self.purges = 0
        self.info_window = c.screen.derived(
            np.array([0, 0]), c.config['info_display_size'],
        )
        genome_size = self.load_genome_into_memory(
            'initial.gen', c.config['memory_size'] // 2
        )
        o.OrganismFull(c.config['memory_size'] // 2, genome_size)
        self.update_info()

    def run(self):
        try:
            self.input_stream()
        except KeyboardInterrupt:
            curses.endwin()
            self.timer.stop()
        except Exception:
            curses.endwin()
            self.timer.stop()
            print(traceback.format_exc())

    def load_genome_into_memory(self, filename: str, address: np.array) -> np.array:
        with open(filename) as genome_file:
            genome = np.array([list(line.strip()) for line in genome_file])
        m.memory.load_genome(genome, address, genome.shape)
        return genome.shape

    def update_position(self, delta):
        m.memory.scroll(delta)
        q.queue.update_all()
        self.update_info()

    def update_info_full(self):
        self.info_window.erase()
        info = ''
        info += 'Cycle      : {}\n'.format(self.cycle)
        info += 'Position   : {}\n'.format(list(m.memory.position))
        info += 'Total      : {}\n'.format(len(q.queue.organisms))
        info += 'Purges     : {}\n'.format(self.purges)
        info += 'Organism   : {}\n'.format(q.queue.index)
        info += q.queue.get_organism().info()
        self.info_window.print(info)

    def update_info_minimal(self):
        self.info_window.erase()
        info = ''
        info += 'Minimal mode '
        info += '[Running]\n' if c.is_running else '[Paused]\n'
        info += 'Cycle      : {}\n'.format(self.cycle)
        info += 'Total      : {}\n'.format(len(q.queue.organisms))
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
        m.memory.clear()
        m.memory = m.memory.toogle() if memory is None else memory.toogle()
        m.memory.update(refresh=True)
        q.queue.toogle_minimal()

    def save_state(self):
        return_to_full = False
        if not self.is_minimal:
            self.toogle_minimal()
            return_to_full = True
        filename = 'snapshots/{}_cycle_{}.snapshot'.format(
            c.config['simulation_name'].lower().replace(' ', '_'), self.cycle
        )
        with open(filename, 'wb') as f:
            state = {
                'cycle': self.cycle,
                'memory': m.memory,
                'queue': q.queue,
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
            if c.config['snapshot_to_load'] == 'last':
                filename = max(glob.glob('snapshots/*'), key=os.path.getctime)
            else:
                filename = c.config['snapshot_to_load']
            with open(filename, 'rb') as f:
                state = pickle.load(f)
                memory = state['memory']
                q.queue = state['queue']
                self.cycle = state['cycle']
        except Exception:
            pass
        if not self.is_minimal or return_to_full:
            self.toogle_minimal(memory)
        else:
            m.memory = memory
            self.update_info_minimal()

    def make_cycle(self):
        if self.cycle % c.config['random_rate'] == 0:
            m.memory.cycle()
        if self.cycle % c.config['cycle_gap'] == 0:
            if m.memory.is_time_to_kill():
                q.queue.kill_organisms()
                self.purges += 1
        if not self.is_minimal:
            q.queue.update_all()
        self.cycle += 1
        self.update_info()

    def input_stream(self):
        while True:
            key = c.screen.get_key()
            if key == ord(' '):
                c.is_running = not c.is_running
                if self.is_minimal:
                    self.update_info_minimal()
            elif key == ord('c') and not c.is_running:
                q.queue.cycle_all()
                self.make_cycle()
            elif key == curses.KEY_DOWN and not self.is_minimal:
                self.update_position(c.config['scroll_step'] * c.deltas['down'])
            elif key == curses.KEY_UP and not self.is_minimal:
                self.update_position(c.config['scroll_step'] * c.deltas['up'])
            elif key == curses.KEY_RIGHT and not self.is_minimal:
                self.update_position(c.config['scroll_step'] * c.deltas['right'])
            elif key == curses.KEY_LEFT and not self.is_minimal:
                self.update_position(c.config['scroll_step'] * c.deltas['left'])
            elif key == ord('d') and not self.is_minimal:
                q.queue.select_next()
                self.update_info()
            elif key == ord('a') and not self.is_minimal:
                q.queue.select_previous()
                self.update_info()
            elif key == ord('m'):
                self.toogle_minimal()
            elif key == ord('p'):
                self.save_state()
            elif key == ord('l'):
                self.load_state()
            elif key == ord('k'):
                q.queue.kill_organisms()
            elif key == -1 and c.is_running:
                q.queue.cycle_all()
                self.make_cycle()


if __name__ == '__main__':
    Fungera().run()
