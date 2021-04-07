import timeit
import time
import curses
from curses import wrapper
import xmlrpc.client
import sys
import os
from anytree.importer import DictImporter
from anytree import RenderTree, AsciiStyle, ContRoundStyle
from anytree import Walker, find_by_attr
from anytree import Node


class Coord:
    x = 0
    y = 0
    height = 0
    width = 0


class Shell:
    pad_height = 4000
    pad_width = 4000
    title_height = 2
    status_height = 2
    title_connect = 'Add/Remove a connection!!!'
    OP_NULL = 0
    OP_ADD = 1
    OP_DEL = 2
    sign = ' ' * 2 + '==>'

    def __init__(self, url):
        self.proxy = xmlrpc.client.ServerProxy(url)
        self.node_coords = []
        self.curses_init()
        self.windows_init()

    def load_midi(self, name, filename):
        with open(filename, 'rb') as f:
            self.proxy.load_midi(name, xmlrpc.client.Binary(f.read()))

    def load_audio(self, name, filename):
        with open(filename, 'rb') as f:
            self.proxy.load_audio(name, xmlrpc.client.Binary(f.read()))

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

    def _input_with_underline(self, win, align, sign='-', letter_len=16):
        _, mx = win.getmaxyx()
        prompt = 'name: '
        _len1 = len(prompt)
        _len = letter_len + _len1
        if align == 'center':
            x = int((mx - _len) / 2)
            win.hline(1, x, sign, _len)
            win.addstr(0, x, prompt)
            return win.getstr(0, x + _len1, _len)
        elif align == 'left':
            win.hline(1, 0, sign, _len)
            win.addstr(0, 0, prompt)
            return win.getstr(0, 0 + _len1, _len)
        elif align == 'right':
            x = mx - _len
            win.hline(1, x, sign, _len)
            win.addstr(0, x, prompt)
            return win.getstr(0, x + _len1, _len)
        else:
            raise ValueError

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

    def input_status(self, align='center'):
        win = self.status_win
        win.clear()
        curses.echo(True)
        _input = self._input_with_underline(win, align)
        curses.noecho()
        win.refresh()
        return _input.decode()

    def anytree_convert(self, data):
        def to_anytree(data, node):
            if isinstance(data, list):
                children = []
                for dat in data:
                    to_anytree(dat, children)
                if children:
                    node['children'] = children
            elif isinstance(data, dict):
                for k, v in data.items():
                    d = {'name': k}
                    to_anytree(v, d)
                    node.append(d)
            else:
                if isinstance(node, list):
                    node.append({'name': data})
                elif isinstance(node, dict):
                    node['children'] = [{'name': data}]
        nodes = []
        root = {'name': 'nodes'}
        to_anytree(data, root)
        for child in root['children']:
            importer = DictImporter()
            tree = importer.import_(child)
            rendered_tree = []
            for pre, _, node in RenderTree(tree, style=ContRoundStyle()):
                rendered_tree.append([pre, node])
            nodes.append([tree, rendered_tree])
        return nodes

    def get_tree_width(self, tree):
        _max_len = 0
        for pre, node in tree:
            s = ''.join([pre, node.name])
            if _max_len < len(s):
                _max_len = len(s)
        return _max_len

    def fill_pad(self, nodes, horizon_padding=2, vertical_padding=6):
        pad = self.pad
        stdscr_width = self.stdscr_width
        pad.clear()
        x, y = 0, 0
        title = 'Nodes:'
        pad.addstr(y, x + horizon_padding, title)
        y += 1
        pad.hline(y, x + horizon_padding, '~', len(title))
        y += 1
        max_height = 0
        for node in nodes:
            coord = Coord()
            _, rendered_tree = node
            _width = self.get_tree_width(rendered_tree)
            coord.width = _width
            coord.height = len(rendered_tree)
            if max_height < coord.height:
                max_height = coord.height
            # exceed the stdscr_width, new line
            if x > 0 and x + _width + vertical_padding > stdscr_width:
                x = 0
                y += max_height + horizon_padding
                max_height = 0
            coord.x, coord.y = x, y
            _y = y
            for prefix, _node in rendered_tree:
                s = ''.join([prefix, _node.name])
                pad.addstr(_y, x + vertical_padding, s)
                _y += 1
            node.append(coord)
            x += _width + vertical_padding

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
                return self.main()
            if ch == ord('y'):
                sys.exit(0)
            elif ch == ord('n'):
                return self.main()

    def full_path(self, node):
        s = ''
        n = node
        while n:
            if s:
                s = n.name + ':' + s
            else:
                s = n.name
            n = n.parent
        return s

    def get_leaf(self, tree, y):
        i = 0
        _len = len(tree)
        while True:
            node = tree[(y + i) % _len]
            if node.is_leaf:
                break
            i += 1
        return y + i

    def draw_arrow(self, y, x):
        pad = self.pad
        nodes = self.nodes
        _len = len(nodes)
        node = nodes[x % _len]
        tree, rendered_tree, coord = node
        _len = len(rendered_tree)
        idx = y % _len
        _y, _x = coord.y + idx, coord.x
        _, _node = rendered_tree[idx]
        pad.addstr(_y, _x, self.sign)
        content_height = self.stdscr_height - self.status_height
        self.pad_y, self.pad_x = 0, 0
        if coord.y + coord.height > content_height:
            self.pad_y = int(content_height / 2)
        pad.refresh(self.pad_y, self.pad_x, self.title_height, 0,
                    self.stdscr_height - self.status_height - 1, self.stdscr_width - 1)
        return _node

    def clear_arrow(self, y, x):
        pad = self.pad
        nodes = self.nodes
        _len = len(nodes)
        node = nodes[x % _len]
        tree, rendered_tree, coord = node
        _len = len(rendered_tree)
        _y, _x = coord.y + y % _len, coord.x
        pad.hline(_y, _x, ' ', len(self.sign))

    def update_content(self, nodes):
        win = self.content_win
        win.clear()
        self.fill_pad(nodes)
        win.refresh()
        self.pad.refresh(self.pad_y, self.pad_x, self.title_height, 0,
                         self.stdscr_height - self.status_height - 1, self.stdscr_width - 1)

    def frame_exception(self, err):
        stdscr = self.stdscr
        self.update_title(err)
        self.update_status('(r)try (q)uit')
        while True:
            ch = stdscr.getch()
            if ch == ord('r'):
                return self.main()
            elif ch == ord('q'):
                self.frame_quit()

    def frame_connect(self, node):
        stdscr = self.stdscr
        self.pair.append(f'{node.root.name}:{node.name}')
        if len(self.pair) < 2:
            return
        src, dst = self.pair
        self.pair = []
        s = f'Link: {src} ==> {dst} ?'
        self.update_title(s)
        self.update_status('(y)es (n)o')
        while True:
            ch = stdscr.getch()
            if ch == ord('y'):
                try:
                    self.proxy.connect(src, dst)
                    s = f'Link: {src} ==> {dst} Succeed !!!'
                except:
                    s = f'Link: {src} ==> {dst} Failed !!!'
                self.update_title(s)
                self.update_status('Press any key ...')
                stdscr.getch()
                self.need_update = True
                break
            elif ch == ord('n'):
                self.need_update = True
                break

    def rm_node(self, node):
        stdscr = self.stdscr
        self.update_title(f'Remove the {node.name} node ?')
        self.update_status('(y)es (n)o')
        while True:
            ch = stdscr.getch()
            if ch == ord('y'):
                try:
                    self.proxy.del_seq(node.name)
                    s = f'Remove the {node.name} node Succeed !!!'
                except:
                    s = f'Remove the {node.name} node Failed !!!'
                self.update_title(s)
                self.update_status('Press any key ...')
                stdscr.getch()
                self.need_update = True
                break
            elif ch == ord('n'):
                self.need_update = True
                break

    def rm_link(self, node):
        stdscr = self.stdscr
        p = node.parent
        src = f'{p.root.name}:{p.name}'
        dst = node.name
        self.update_title(f'Remove {src} ==> {dst} ?')
        self.update_status('(y)es (n)o')
        while True:
            ch = stdscr.getch()
            if ch == ord('y'):
                try:
                    self.proxy.disconnect(src, dst)
                    s = f'Remove {src} ==> {dst} Succeed !!!'
                except:
                    s = f'Remove {src} ==> {dst} Failed !!!'
                self.update_title(s)
                self.update_status('Press any key ...')
                stdscr.getch()
                self.need_update = True
                break
            elif ch == ord('n'):
                self.need_update = True
                break

    def frame_disconnect(self, node):
        if node.is_root:
            self.rm_node(node)
        elif node.is_leaf and node.depth == 4:
            self.rm_link(node)

    def list_files(self, startpath):
        startpath = os.path.abspath(startpath)
        node = None
        last_level = 0
        for root, _, files in os.walk(startpath):
            level = root.replace(startpath, '').count(os.sep)
            _dir = os.path.basename(root)
            if not node:
                node = Node(_dir, type='directory')
            else:
                if level > last_level:
                    node = Node(_dir, parent=node, type='directory')
                if level < last_level:
                    node = Node(_dir, parent=node.parent.parent,
                                type='directory')
                else:
                    if node.name != _dir:
                        node = Node(_dir, parent=node.parent, type='directory')
            last_level = level
            children = []
            for f in files:
                children.append(Node(f, type='file', filepath=f'{root}/{f}'))
            if children:
                node.children = children
        nodes = []
        rendered_tree = []
        tree = node.root
        for pre, _, node in RenderTree(tree, style=ContRoundStyle()):
            rendered_tree.append([pre, node])
        nodes.append([tree, rendered_tree])
        return nodes

    def browser(self, path):
        stdscr = self.stdscr
        nodes = self.list_files(path)
        self.update_content(nodes)
        self.nodes = nodes
        y, x = 0, 0
        y1, x1 = 0, 0
        while True:
            self.clear_arrow(y1, x1)
            node = self.draw_arrow(y, x)
            info = self.full_path(node)
            self.update_title(info)
            y1, x1 = y, x
            ch = stdscr.getch()
            if ch == ord(' '):
                return node.filepath
            # navigation
            if ch == ord('k'):
                y -= 1
            elif ch == ord('j'):
                y += 1
            elif ch == ord('h'):
                x -= 1
            elif ch == ord('l'):
                x += 1
            if x != x1:
                y = 0

    def frame_add(self):
        stdscr = self.stdscr
        self.update_title('Adding new Node...')
        self.update_status('(a)udio (m)idi (r)ecorder (s)yth (b)ack')
        while True:
            ch = stdscr.getch()
            if ch == ord('a'):
                filepath = self.browser('tests')
                name = self.input_status()
                self.load_audio(name, filepath)
                self.update_status('Press any key ...')
                stdscr.getch()
                self.need_update = True
                break
            elif ch == ord('m'):
                filepath = self.browser('tests')
                name = self.input_status()
                self.load_midi(name, filepath)
                self.update_status('Press any key ...')
                stdscr.getch()
                self.need_update = True
                break
            elif ch == ord('r'):
                name = self.input_status()
                self.update_status('Press any key ...')
                stdscr.getch()
                self.need_update = True
                break
            elif ch == ord('s'):
                name = self.input_status()
                try:
                    self.proxy.add_seq(name)
                    self.update_title(f'Add {name} SUCCESS!!!')
                except:
                    self.update_title(f'Add {name} FAILED!!!')
                self.update_status('Press any key ...')
                stdscr.getch()
                self.need_update = True
                break
            elif ch == ord('b'):
                self.need_update = True
                return

    def frame_player(self):
        stdscr = self.stdscr
        bpm = self.proxy.get_bpm()
        state = self.proxy.get_transport_state()
        self.update_status('(p)lay (s)top (b)ack')
        need_update = True
        while True:
            if need_update:
                self.update_title(f'BPM: {bpm}, STATUS: {state}')
                need_update = False

            ch = stdscr.getch()
            if ch == ord('p'):
                self.proxy.play()
                time.sleep(0.5)
                state = self.proxy.get_transport_state()
                need_update = True
            elif ch == ord('s'):
                self.proxy.stop()
                time.sleep(0.5)
                state = self.proxy.get_transport_state()
                need_update = True
            elif ch == ord('b'):
                self.need_update = True
                break
            elif ch == ord('j'):
                bpm -= 1
                self.proxy.change_bpm(bpm)
                need_update = True
            elif ch == ord('k'):
                bpm += 1
                self.proxy.change_bpm(bpm)
                need_update = True

    def reload_main(self):
        try:
            data = self.proxy.get_all_nodes()
        except ConnectionRefusedError:
            self.frame_exception('[Error] Connection refused!!!')
        except xmlrpc.client.Fault as err:
            err = 'Fault: {}, {}'.format(err.faultCode, err.faultString)
            self.frame_exception(err)
        self.update_title('Welcome to Coderband!!!')
        self.update_status('(c)onnect (d)isconnect (n)ew (r)load (p)layer (q)uit')
        self.nodes = self.anytree_convert(data)
        self.update_content(self.nodes)
        self.need_update = False

    def main(self):
        stdscr = self.stdscr
        stdscr.clear()
        stdscr.refresh()
        self.pair = []
        self.reload_main()
        # arrow new, old pos
        y, x = 0, 0
        y1, x1 = 0, 0
        while True:
            if self.need_update:
                self.reload_main()
                y, x = 0, 0
                y1, x1 = 0, 0
            self.clear_arrow(y1, x1)
            node = self.draw_arrow(y, x)
            info = self.full_path(node)
            self.update_title(info)
            y1, x1 = y, x
            ch = stdscr.getch()
            if self.on_resize(ch):
                self.need_update = True
            if ch == ord('r'):
                self.need_update = True
            elif ch == ord('n'):
                self.frame_add()
            elif ch == ord('q'):
                self.frame_quit()
            elif ch == ord('c'):
                self.frame_connect(node)
            elif ch == ord('d'):
                self.frame_disconnect(node)
            elif ch == ord('p'):
                self.frame_player()
            # navigation
            if ch == ord('k'):
                y -= 1
            elif ch == ord('j'):
                y += 1
            elif ch == ord('h'):
                x -= 1
            elif ch == ord('l'):
                x += 1
            if x != x1:
                y = 0


def main(host):
    shell = Shell(host)
    try:
        shell.main()
    except KeyboardInterrupt:
        shell.close()
    finally:
        shell.close()


def demo(url):
    #proxy = xmlrpc.client.ServerProxy(url)
    #nodes = proxy.get_all_nodes()
    def list_files(startpath):
        startpath = os.path.abspath(startpath)
        node = None
        last_level = 0
        for root, _, files in os.walk(startpath):
            level = root.replace(startpath, '').count(os.sep)
            _dir = os.path.basename(root)
            if not node:
                node = Node(_dir, type='directory')
            else:
                if level > last_level:
                    node = Node(_dir, parent=node, type='directory')
                if level < last_level:
                    node = Node(_dir, parent=node.parent.parent,
                                type='directory')
                else:
                    if node.name != _dir:
                        node = Node(_dir, parent=node.parent, type='directory')
            last_level = level
            children = []
            for f in files:
                children.append(Node(f, type='file', filepath=f'{root}/{f}'))
            if children:
                node.children = children
        return node.root
    root = list_files(sys.argv[1])
    for pre, _, node in RenderTree(root, style=ContRoundStyle):
        # print(f'{pre}{node.name}')
        if node.is_leaf and node.type == 'file':
            print(node.filepath)


if __name__ == '__main__':
    host = 'http://localhost:8000'
    if 1:
        main(host)
    else:
        demo(host)
