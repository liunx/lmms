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
    pad_height = 4000
    pad_width = 4000
    input_len = 16

    def __init__(self, url):
        self.running = True
        self.mods = {}
        self.midi_ports = {}
        self.audio_ports = {}
        self.actions = {}
        self.frame_handler = self.frame_main
        self.proxy = xmlrpc.client.ServerProxy(url)
        self.curses_init()

    def curses_init(self):
        self.stdscr = curses.initscr()
        curses.noecho()
        curses.cbreak()
        curses.start_color()
        curses.use_default_colors()
        curses.curs_set(0)
        self.stdscr.keypad(True)
        self.pad = curses.newpad(self.pad_height, self.pad_width)

    def close(self):
        curses.nocbreak()
        self.stdscr.keypad(False)
        curses.echo()
        curses.endwin()

    def _fill_ports(self, ports):
        l = []
        for k, v in ports.items():
            data = v['input']
            if len(data) > 0:
                s = f'{k}:in:{{'
                l.append(s)
                i = 0
                while i < len(data) - 1:
                    s = f'{data[i]},'
                    l.append(s)
                    i += 1
                s = f'{data[i]}}}'
                l.append(s)
            data = v['output']
            if len(data) > 0:
                s = f'{k}:out:{{'
                l.append(s)
                i = 0
                while i < len(data) - 1:
                    s = f'{data[i]},'
                    l.append(s)
                    i += 1
                s = f'{data[i]}}}'
                l.append(s)
        return l

    def dialog(self, title):
        stdscr = self.stdscr
        _len = len(title)
        x = int((self.stdscr_x - _len) / 2)
        stdscr.hline(0, x, '-', _len)
        stdscr.addstr(1, x, title)
        curses.echo()
        curses.curs_set(1)
        prompt = '> '
        x = int((self.stdscr_x - (self.input_len + len(prompt))) / 2)
        # clear action line
        stdscr.hline(self.stdscr_y - 2, 0, ' ', self.stdscr_x)
        stdscr.addstr(self.stdscr_y - 2, x, prompt)
        ans = stdscr.getstr(self.stdscr_y - 2, x + len(prompt), self.input_len)
        curses.noecho()
        curses.curs_set(0)
        stdscr.refresh()
        return ans.decode()

    def fill_content(self, content):
        pad = self.pad
        pad.clear()
        self._layout(pad, 2, content)
        pad.refresh(self.pos_y, self.pos_x, 2, 0,
                    self.stdscr_y - 3, self.stdscr_x - 1)

    def frame_main(self):
        content = {'layout': 'vertical', 'align': 'left', 'data': []}
        self.frame = {
            'title': 'Welcome to Coderband!!!',
            'content': content,
            'actions': ['(a)dd', '(c)onnect', '(d)isconnect',  '(r)efresh', '(q)uit'],
        }
        self.actions = {'a': self.frame_add, 'c': self.frame_connect,
                        'd': self.frame_disconnect, 'r': self.frame_main, 'q': self.frame_quit}
        # fill content
        ports = self.get_audio_ports()
        l = ['Audio Ports:']
        content['data'].append(l + self._fill_ports(ports))
        ports = self.get_midi_ports()
        l = ['Midi Ports:']
        content['data'].append(l + self._fill_ports(ports))
        # only clear the pad when update
        self.pad.clear()

    def frame_add(self):
        self.frame = {
            'title': 'Add Synth/Effect',
            'content': [],
            'actions': ['(s)ynth', '(e)ffect', '(b)ack']
        }
        self.actions = {'b': self.frame_main}

    def frame_audio_connect(self):
        content = {'layout': 'vertical', 'align': 'left', 'data': []}
        out_ports = ['out ports:']
        out_idx = 0
        in_ports = ['in ports:']
        in_idx = 0
        ports = self.get_audio_ports()
        for k, v in ports.items():
            for p in v['input']:
                in_idx += 1
                in_ports.append(f'{in_idx}.{k}:{p}')
            for p in v['output']:
                out_idx += 1
                out_ports.append(f'{out_idx}.{k}:{p}')
        content['data'] = [out_ports, in_ports]
        self.fill_content(content)
        res = self.dialog('Please input your selection!!!')
        try:
            _out, _in = res.split(',')
            _outp, _inp = out_ports[int(_out)], in_ports[int(_in)]
            self.connect(_outp, _inp)
        except:
            pass
        # return back to frame connect
        self.frame_connect()

    def frame_midi_connect(self):
        # return back to frame connect
        self.frame_connect()

    def frame_connect(self):
        content = {'layout': 'vertical', 'align': 'left', 'data': []}
        self.frame = {
            'title': 'Do jack connect',
            'content': content,
            'actions': ['(a)udio', '(m)idi', '(b)ack']
        }
        self.actions = {'a': self.frame_audio_connect,
                        'm': self.frame_midi_connect, 'b': self.frame_main}

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

    def connect(self, out_p, in_p):
        self.proxy.connect(out_p, in_p)

    def get_mods(self):
        pass

    def _max_len(self, data):
        _max = 0
        for dat in data:
            if _max < len(dat):
                _max = len(dat)
        return _max

    def _layout(self, pad, y, content, padding=0, gap=4):
        pad_y, pad_x = pad.getmaxyx()
        align = content['align']
        layout = content['layout']
        data = content['data']
        max_len = 0
        if layout == 'vertical':
            for dat in data:
                max_len += self._max_len(dat)
                max_len += padding
        elif layout == 'horizon':
            for dat in data:
                m = self._max_len(dat)
                if max_len < m:
                    max_len = m
            max_len += padding
        else:
            raise ValueError('Unknown layout: {}!'.format(layout))
        x = int((pad_x - max_len + gap) / 2)
        for dat in data:
            _y = y
            title = dat[0]
            pad.addstr(_y, x, title)
            _y += 1
            pad.hline(_y, x, '-', len(title))
            x += padding
            _y += 1
            _max = 0
            for _dat in dat[1:]:
                if _max < len(_dat):
                    _max = len(_dat)
                pad.addstr(_y, x, _dat)
                _y += 1
            x += _max
            x += gap

    def draw(self, padding, gap):
        stdscr = self.stdscr
        pad = self.pad
        frame = self.frame
        title = frame['title']
        x = int((self.stdscr_x - len(title)) / 2)
        y = 1
        stdscr.addstr(y, x, title)
        stdscr.hline(0, x, '-', len(title))
        y += 2
        # content
        content = frame['content']
        if content:
            self._layout(pad, 1, content, padding=padding, gap=gap)
        # actions
        actions = frame['actions']
        s = ''
        i = 0
        while i < len(actions) - 1:
            s += actions[i]
            s += ', '
            i += 1
        s += actions[i]
        x = int((self.stdscr_x - len(s)) / 2)
        stdscr.addstr(self.stdscr_y - 2, x, s)
        stdscr.hline(self.stdscr_y - 3, x, '-', len(s))

    def action_handler(self, ch):
        if ch in self.actions:
            self.frame_handler = self.actions[ch]

    def process(self):
        stdscr = self.stdscr
        gap = 8
        padding = 2
        pad = self.pad
        self.stdscr_y, self.stdscr_x = stdscr.getmaxyx()
        self.pad_y, self.pad_x = pad.getmaxyx()
        self.pos_y = 0
        self.pos_x = int((self.pad_x + gap - self.stdscr_x) / 2)
        stepping = 3
        while True:
            if self.frame_handler:
                self.frame_handler()
                self.frame_handler = None
            if not self.running:
                break
            stdscr.clear()
            self.draw(padding, gap)
            stdscr.refresh()
            # leave 2 for title, 2 for actions
            pad.refresh(self.pos_y, self.pos_x, 2, 0, self.stdscr_y -
                        3, self.stdscr_x - 1)
            ch = stdscr.getch()
            if ch == curses.KEY_RESIZE:
                self.stdscr_y, self.stdscr_x = stdscr.getmaxyx()
                self.pos_x = int((self.pad_x + gap - self.stdscr_x) / 2)
                continue
            self.action_handler(chr(ch))
            # navigate
            if ch == curses.KEY_UP:
                self.pos_y -= stepping
                if self.pos_y < 0:
                    self.pos_y = 0
            elif ch == curses.KEY_DOWN:
                self.pos_y += stepping
                if self.pos_y > self.pad_y:
                    self.pos_y = self.pad_y - 1
            elif ch == curses.KEY_LEFT:
                self.pos_x -= stepping
                if self.pos_x < 0:
                    self.pos_x = 0
            elif ch == curses.KEY_RIGHT:
                self.pos_x += stepping
                if self.pos_x > self.pad_x:
                    self.pos_x = self.pad_x - 1

    def run(self):
        pass


if __name__ == '__main__':
    shell = Shell('http://localhost:8000')
    shell.process()
    shell.close()
