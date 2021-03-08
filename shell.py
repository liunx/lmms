import timeit
import time
import curses
from curses import wrapper
import xmlrpc.client
import sys
from anytree.importer import DictImporter
from anytree import RenderTree, AsciiStyle


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


class Coord:
    x = 0
    y = 0


class Shell:
    pad_height = 4000
    pad_width = 4000
    title_height = 2
    status_height = 2

    def __init__(self, url):
        self.proxy = xmlrpc.client.ServerProxy(url)
        self.node_coords = []
        self.curses_init()
        self.windows_init()

    def curses_init(self):
        stdscr = curses.initscr()
        curses.noecho()
        curses.cbreak()
        curses.start_color()
        curses.use_default_colors()
        curses.curs_set(0)
        stdscr.keypad(True)
        self.stdscr = stdscr

    def windows_init(self):
        height, width = self.stdscr.getmaxyx()
        self.title_win = curses.newwin(self.title_height, width, 0, 0)
        self.content_win = curses.newwin(
            height - (self.title_height + self.status_height), width, self.title_height, 0)
        self.status_win = curses.newwin(
            self.status_height, width, height - self.status_height, 0)
        self.pad = curses.newpad(self.pad_height, self.pad_width)
        self.stdscr_height = height
        self.stdscr_width = width
        self.pad_y = 0
        self.pad_x = 0

    def close(self):
        curses.nocbreak()
        self.stdscr.keypad(False)
        curses.echo()
        curses.endwin()

    def _fill_with_underline(self, win, data, align, sign='-'):
        _, mx = win.getmaxyx()
        _len = len(data)
        if align == 'center':
            x = int((mx - _len) / 2)
            win.addstr(0, x, data)
            win.hline(1, x, sign, _len)
        elif align == 'left':
            win.addstr(0, 0, data)
            win.hline(1, 0, sign, _len)
        elif align == 'right':
            x = mx - _len
            win.addstr(0, x, data)
            win.hline(1, x, sign, _len)
        else:
            raise ValueError
        pass

    def update_title(self, data, align='center'):
        win = self.title_win
        win.clear()
        self._fill_with_underline(win, data, align)
        win.refresh()

    def update_status(self, data, align='center'):
        win = self.status_win
        win.clear()
        self._fill_with_underline(win, data, align, sign=' ')
        win.refresh()

    def tree_format(self, data, l, branch, coords=[], padding=3):
        if isinstance(data, dict):
            ll = []
            for k, v in data.items():
                coords.append(k)
                if branch:
                    ll.append(branch + '-' * padding + k)
                    _branch = branch + ' ' * padding + '|'
                else:
                    ll.append(k)
                    _branch = ' ' * padding + '|'
                self.tree_format(v, ll, _branch, coords=coords)
            l += ll
        elif isinstance(data, list):
            ll = []
            for dat in data:
                self.tree_format(dat, ll, branch, coords=coords)
            l += ll
        else:
            coords.append(data)
            l.append(branch + '-' * padding + data)

    def fill_pad(self, pad, data, padding=4):
        height = self.stdscr_height - self.title_height - self.status_height
        width = self.stdscr_width
        lines = []
        node_coords = []
        if isinstance(data, dict):
            l = []
            coords = []
            self.tree_format(data, l, None, coords=coords)
            lines.append(l)
            node_coords.append({'coords': coords})
        elif isinstance(data, list):
            for dat in data:
                l = []
                coords = []
                self.tree_format(dat, l, None, coords=coords)
                lines.append(l)
                node_coords.append({'coords': coords})
        x, y = 0, 0
        max_y = 0
        pad.clear()
        for line, coords in zip(lines, node_coords):
            max_len = self._max_len(line)
            if x + max_len > width:
                x = 0
                y = max_y
            pad.hline(y, x, ' ', 1)
            y += 1
            #pad.addstr(y, x, '==>')
            coords['y'] = y
            coords['x'] = x
            for s in line:
                pad.addstr(y, x + padding, s)
                y += 1
            x += max_len + padding
            if max_y < y:
                max_y = y
            y = 0
        # end for loop
        self.node_coords = node_coords
        self.node_index = 0

    def update_content(self, data):
        win = self.content_win
        pad = self.pad
        win.clear()
        pad.clear()
        self.fill_pad(pad, data)
        win.refresh()
        pad.refresh(self.pad_y, self.pad_x, self.title_height, 0,
                    self.stdscr_height - self.status_height - 1, self.stdscr_width - 1)

    def _max_len(self, data):
        _max = 0
        for dat in data:
            if _max < len(dat):
                _max = len(dat)
        return _max

    def on_resize(self, ch):
        if ch == curses.KEY_RESIZE:
            self.windows_init()
            return True
        return False

    def frame_quit(self):
        stdscr = self.stdscr
        self.update_title('Exit from the program?')
        self.update_status('(y)es (n)o')
        stdscr.refresh()
        while True:
            ch = stdscr.getch()
            if self.on_resize(ch):
                self.main()
            if ch == ord('y'):
                sys.exit(0)
                self.running = False
                break
            elif ch == ord('n'):
                self.main()

    def draw_arrow(self, new, old):
        sign = '==>'
        pad = self.pad
        nodes_len = len(self.node_coords)
        coord = self.node_coords[old.y % nodes_len]
        pad.addstr(coord['y'], coord['x'], ' ' * len(sign))
        coord = self.node_coords[new.y % nodes_len]
        self.update_title(coord['coords'][0])
        pad.addstr(coord['y'], coord['x'], sign)
        pad.refresh(self.pad_y, self.pad_x, self.title_height, 0,
                    self.stdscr_height - self.status_height - 1, self.stdscr_width - 1)

    def frame_connection(self):
        stdscr = self.stdscr
        stdscr.refresh()
        self.update_title('Create a connection!!!')
        self.update_status('(b)ack')
        _new = Coord()
        _old = Coord()
        while True:
            self.draw_arrow(_new, _old)
            _old.y, _old.x = _new.y, _new.x
            ch = stdscr.getch()
            if self.on_resize(ch):
                self.main()
            if ch == ord('b'):
                self.main()
            if ch == curses.KEY_UP:
                _new.y -= 1
            elif ch == curses.KEY_DOWN:
                _new.y += 1
            elif ch == curses.KEY_LEFT:
                _new.x -= 1
            elif ch == curses.KEY_RIGHT:
                _new.x += 1

    def main(self):
        stdscr = self.stdscr
        data = self.proxy.get_all_nodes()
        stdscr.clear()
        stdscr.refresh()
        self.update_title('Welcome to Coderband!!!')
        self.update_content(data)
        self.update_status('(a)dd (c)onnect (d)isconnect (r)efresh (q)uit')
        self.running = True
        while self.running:
            ch = stdscr.getch()
            if self.on_resize(ch):
                self.main()
            if ch == ord('r'):
                self.main()
            if ch == ord('c'):
                self.frame_connection()
            elif ch == ord('q'):
                self.frame_quit()


'''
Nodes:
~~~~~
==> Calf Studio Gear:
        |----Audio (a)
        |     |----Input (i)
        |     |     |----flanger In #1 (1)
        |     |     |----flanger In #2 (2)
        |     |----Output (o)
        |     |     |----monosynth Out #1 (1)
        |     |     |----monosynth Out #2 (2)
        |     |     |----flanger In #1 (3)
        |     |     |----flanger In #2 (4)
        |----MIDI (m)
        |     |----Input (i)
        |     |     |----Automation MIDI In (1)
        |     |     |----monosynth MIDI In (2)
        |     |----Output (o)
        |     |     |----Automation MIDI Out (1)
        |     |     |----monosynth MIDI Out (2)

Connections:
~~~~~~~~~~

==> Calf Studio Gear:A:O:monosynth Out #1 ==> Calf Studio Gear:A:I:flanger In #1
        Calf Studio Gear:A:O:monosynth Out #1 ==> Calf Studio Gear:A:I:flanger In #1

'''


def main(host):
    shell = Shell(host)
    try:
        shell.main()
    except KeyboardInterrupt:
        shell.close()
    finally:
        shell.close()


def to_anytree(data, node):
    if isinstance(data, list):
        children = []
        for dat in data:
            to_anytree(dat, children)
        node['children'] = children
    elif isinstance(data, dict):
        for k, v in data.items():
            d = {'name': k}
            to_anytree(v, d)
            node.append(d)
    else:
        node.append({'name': data})


def debug(url):
    #proxy = xmlrpc.client.ServerProxy(url)
    #nodes = proxy.get_all_nodes()
    nodes = [{'system': [{'audio': [{'input': ['playback_1', 'playback_2']},
                                    {'output': ['capture_1', 'monitor_1', 'monitor_2']}]}]}]

    #nodes = [{'system': [{'audio': []}]}]
    root = {'name': 'nodes'}
    to_anytree(nodes, root)
    print(root)
    if 1:
        importer = DictImporter()
        tree = importer.import_(root)
        print(RenderTree(tree, style=AsciiStyle))


if __name__ == '__main__':
    host = 'http://localhost:8000'
    if 0:
        main(host)
    else:
        debug(host)
