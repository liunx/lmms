import timeit
import time
import curses
from curses import wrapper
import xmlrpc.client


def load_midi(s, name, filename):
    with open(filename, 'rb') as f:
        t = timeit.default_timer()
        s.load_midi(name, xmlrpc.client.Binary(f.read()))
        print(timeit.default_timer() - t)


def load_audio(s, name, filename):
    with open(filename, 'rb') as f:
        t = timeit.default_timer()
        s.load_audio(name, xmlrpc.client.Binary(f.read()))
        print(timeit.default_timer() - t)


def show_frame(stdscr, frame, w, h):
    title = frame['title']
    x = int((w - len(title)) / 2)
    y = 0
    stdscr.addstr(y, x, title)

frame_main = {
    'title': 'Welcome to Coderband!!!',
    'actions': ['add', 'connect', 'disconnect',  'show'],
}


def shell(stdscr):
    curses.use_default_colors()
    curses.curs_set(0)
    proxy = xmlrpc.client.ServerProxy('http://localhost:8000')
    _frame = frame_main
    _w, _h = stdscr.getmaxyx()
    while True:
        stdscr.clear()
        stdscr.border()
        show_frame(stdscr, _frame, _w, _h)
        stdscr.refresh()
        ch = stdscr.getch()
        if ch == ord('q'):
            print("Bye!!!")
            break
        if ch == curses.KEY_RESIZE:
            _w, _h = stdscr.getmaxyx()
            continue
        if ch == ord('a'):
            pass
        elif ch == ord('c'):
            pass
        elif ch == ord('d'):
            pass
        elif ch == ord('l'):
            pass


def demo():
    s.add_synth('synth_01')
    s.add_seq('seq')
    while True:
        s.play(90)
        s.stop()


if __name__ == '__main__':
    wrapper(shell)
