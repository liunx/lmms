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


class Shell:

    def __init__(self, url):
        self.running = True
        self.mods = {}
        self.midi_ports = {}
        self.audio_ports = {}
        self.actions = {}
        self.frame_handler = self.frame_main
        self.proxy = xmlrpc.client.ServerProxy(url)

    # frame handlers
    def frame_main(self):
        content = self.get_all_ports()
        self.frame = {
            'title': 'Welcome to Coderband!!!',
            'content': content,
            'actions': ['(a)dd', '(c)onnect', '(d)isconnect',  '(r)efresh', '(q)uit'],
        }
        self.actions = {'a': self.frame_add, 'c': self.frame_connect,
                        'd': self.frame_disconnect, 'r': self.frame_main, 'q': self.frame_quit}

    def frame_add(self):
        self.frame = {
            'title': 'Add Synth/Effect',
            'content': [],
            'actions': ['(s)ynth', '(e)ffect', '(b)ack']
        }
        self.actions = {'b': self.frame_main}

    def frame_connect(self):
        self.frame = {
            'title': 'Do jack connect',
            'content': [],
            'actions': ['(a)udio', '(m)idi', '(b)ack']
        }
        self.actions = {'b': self.frame_main}

    def frame_disconnect(self):
        self.frame = {
            'title': 'Do jack disconnect',
            'content': [],
            'actions': ['(a)udio', '(m)idi', '(b)ack']
        }
        self.actions = {'b': self.frame_main}

    def frame_quit(self):
        self.frame = {
            'title': 'Exit from the program, are you sure?',
            'content': [],
            'actions': ['(y)es', '(n)o']
        }
        self.actions = {'y': self._frame_quit, 'n': self.frame_main}

    def _frame_quit(self):
        self.running = False

    def get_all_ports(self):
        l = []
        ports = self.proxy.get_all_ports()
        for p in ports:
            l.append(p['name'])
        return l

    def get_audio_ports(self):
        ports = self.proxy.get_audio_ports()
        return ports

    def get_midi_ports(self):
        ports = self.proxy.get_midi_ports()
        return ports

    def get_mods(self):
        pass

    def display(self, stdscr):
        frame = self.frame
        title = frame['title']
        x = int((self.width - len(title)) / 2)
        y = 1
        stdscr.addstr(y, x, title)
        stdscr.hline(0, x, '-', len(title))
        y += 2
        # content
        content = frame['content']
        _max = 0
        for i in content:
            if _max < len(i):
                _max = len(i)
        x = int((self.width - _max) / 2)
        for i in content:
            stdscr.addstr(y, x, i)
            y += 1
        # actions
        actions = frame['actions']
        s = ''
        i = 0
        while i < len(actions) - 1:
            s += actions[i]
            s += ', '
            i += 1
        s += actions[i]
        x = int((self.width - len(s)) / 2)
        stdscr.addstr(self.height - 2, x, s)
        stdscr.hline(self.height - 3, x, '-', len(s))

    def action_handler(self, ch):
        if ch in self.actions:
            self.frame_handler = self.actions[ch]

    def process(self, stdscr):
        curses.use_default_colors()
        curses.curs_set(0)
        self.height, self.width = stdscr.getmaxyx()
        while True:
            if self.frame_handler:
                self.frame_handler()
                self.frame_handler = None
            if not self.running:
                break
            stdscr.clear()
            self.display(stdscr)
            stdscr.refresh()
            ch = stdscr.getch()
            if ch == curses.KEY_RESIZE:
                self.height, self.width = stdscr.getmaxyx()
                continue
            self.action_handler(chr(ch))


'''
                                          all ports
                                          ----------
 Audio:                                                          Midi:                                                       
 -------                                                           ------
    system:in:{playback_1, playback_2}         system:in:{playback_1}
    system:out:{capture_1}
    work:out:{left, right}

Connection:
-------------
    work:{left,right} --> system:{playback_1, playback_2}
'''

if __name__ == '__main__':
    shell = Shell('http://localhost:8000')
    wrapper(shell.process)
