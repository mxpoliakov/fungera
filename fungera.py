import curses
import traceback
import numpy as np
from window import Window
from memory import Memory
from organism import Organism, Queue
from config import Color, INFO_PANEL_SIZE, INITIAL_ORGANISM_POSITION


class Fungera:
    def __init__(self):
        self.screen = None
        self.init_curses()

        self.queue = Queue()
        self.cycle = 0

        self.info_window = self.screen.derived(np.array([0, 0]), INFO_PANEL_SIZE,)
        self.memory = Memory(self.screen)
        genome_size = self.load_genome_into_memory(
            'initial.gen', INITIAL_ORGANISM_POSITION
        )
        Organism(self.memory, self.queue, INITIAL_ORGANISM_POSITION, genome_size)
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
        curses.init_pair(Color.CHILD, curses.COLOR_WHITE, 33)
        curses.init_pair(Color.IP, curses.COLOR_WHITE, 117)
        curses.init_pair(Color.STANDARD, curses.COLOR_WHITE, -1)

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
        self.info_window.print('Cycle      : {}\n'.format(self.cycle))
        self.info_window.print('Position   : {}\n'.format(list(self.memory.position)))
        self.info_window.print('Organism   : {}\n'.format(self.queue.index))
        self.queue.get_organism().update_info(self.info_window)

    def make_cycle(self):
        self.queue.cycle_all()
        self.cycle += 1
        self.update_info()

    def input_stream(self):
        while True:
            key = self.screen.get_key()
            if key == ord('c'):
                self.make_cycle()
            elif key == ord(' '):
                _ = [self.make_cycle() for _ in range(10000)]
            elif key == curses.KEY_DOWN:
                self.update_position(np.array([5, 0]))
            elif key == curses.KEY_UP:
                self.update_position(np.array([-5, 0]))
            elif key == curses.KEY_RIGHT:
                self.update_position(np.array([0, 5]))
            elif key == curses.KEY_LEFT:
                self.update_position(np.array([0, -5]))
            elif key == ord('d'):
                self.queue.select_next()
                self.update_info()
            elif key == ord('a'):
                self.queue.select_previous()
                self.update_info()


if __name__ == '__main__':
    Fungera().run()
