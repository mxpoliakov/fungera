import curses
import traceback
import numpy as np
from modules.window import Window
from modules.memory import Memory
from modules.queue import Queue
from modules.organism import Organism
from modules.common import (
    Color,
    INFO_SIZE,
    DELTA,
    SCROLL_STEP,
    MEMORY_SIZE,
)


class Fungera:
    def __init__(self):
        self.screen = None
        self.init_curses()

        self.queue = Queue()
        self.cycle = 0
        self.running = False

        self.info_window = self.screen.derived(np.array([0, 0]), INFO_SIZE,)
        self.memory = Memory(self.screen)
        genome_size = self.load_genome_into_memory('initial.gen', MEMORY_SIZE // 2)
        Organism(self.memory, self.queue, MEMORY_SIZE // 2, genome_size)
        self.update_info()

    def init_curses(self):
        self.screen = Window(curses.initscr())
        self.screen.setup()

        curses.noecho()
        curses.cbreak()
        curses.curs_set(0)

        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(Color.SELECTED_PARENT, curses.COLOR_WHITE, 126)
        curses.init_pair(Color.SELECTED_IP, curses.COLOR_WHITE, 160)
        curses.init_pair(Color.SELECTED_CHILD, curses.COLOR_WHITE, 128)
        curses.init_pair(Color.PARENT, curses.COLOR_WHITE, 27)
        curses.init_pair(Color.IP, curses.COLOR_WHITE, 117)
        curses.init_pair(Color.CHILD, curses.COLOR_WHITE, 33)

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

    def update_info(self):
        self.info_window.erase()
        info = ''
        info += 'Cycle      : {}\n'.format(self.cycle)
        info += 'Position   : {}\n'.format(list(self.memory.position))
        info += 'Organism   : {}\n'.format(self.queue.index)
        info += self.queue.get_organism().info()
        self.info_window.print(info)

    def make_cycle(self):
        self.queue.cycle_all()
        self.cycle += 1
        self.update_info()

    def input_stream(self):
        while True:
            key = self.screen.get_key()
            if key == -1 and self.running:
                self.make_cycle()
            elif key == ord('c') and not self.running:
                self.make_cycle()
            elif key == ord(' '):
                self.running = not self.running
            elif key == curses.KEY_DOWN:
                self.update_position(SCROLL_STEP * DELTA['DOWN'])
            elif key == curses.KEY_UP:
                self.update_position(SCROLL_STEP * DELTA['UP'])
            elif key == curses.KEY_RIGHT:
                self.update_position(SCROLL_STEP * DELTA['RIGHT'])
            elif key == curses.KEY_LEFT:
                self.update_position(SCROLL_STEP * DELTA['LEFT'])
            elif key == ord('d'):
                self.queue.select_next()
                self.update_info()
            elif key == ord('a'):
                self.queue.select_previous()
                self.update_info()


if __name__ == '__main__':
    Fungera().run()
