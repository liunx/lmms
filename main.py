import sys
import pkgutil
import importlib
import numpy as np
from parser import MyLexer

from analysis import Analysis
from convert import Midi
from midi import Synth, Sequencer, TimebaseMaster
import mods.beats
import mods.rhythm
import mods.melody
import xmlrpc.client
from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.server import SimpleXMLRPCRequestHandler
import jack
from mido import MidiFile
import tempfile


class RequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ('/RPC2',)


class Matrix:
    key_range = 88
    key_start = 21
    key_stop = 108

    def __init__(self, full_matrix, input_matrix):
        self._full_matrix = full_matrix
        self._input_matrix = input_matrix


class CoderBand:
    # 88 keyboard
    key_range = 88
    key_start = 21
    key_stop = 108

    def __init__(self):
        self.lex = MyLexer()
        self.lex.build(debug=False)
        self.beats_handlers = {}
        self.rhythm_handlers = {}
        self.melody_handlers = {}
        self.load_mods()

    def load_mods(self):
        for m in pkgutil.iter_modules(mods.beats.__path__):
            l = importlib.import_module('mods.beats.' + m.name)
            self.beats_handlers[m.name] = l.callbacks
        for m in pkgutil.iter_modules(mods.rhythm.__path__):
            l = importlib.import_module('mods.rhythm.' + m.name)
            self.rhythm_handlers[m.name] = l.callbacks
        for m in pkgutil.iter_modules(mods.beats.__path__):
            l = importlib.import_module('mods.beats.' + m.name)
            self.beats_handlers[m.name] = l.callbacks

    def parse(self, filename):
        result = {}
        with open(filename) as f:
            self.lex.process(f.read())
            result = self.lex.result
        return self.analysis(result)

    def fill_note(self, note, matrix):
        _matrix = matrix[0]
        offset = int(note['offset'])
        idx = int(note['midi'] - self.key_start)
        _len = int(note['len'])
        i = 0
        while i < _len - 1:
            _matrix[offset + i][idx] = 3
            i += 1
        _matrix[offset + i][idx] = 2

    def find_midis(self, matrix, offset_start=0, offset_len=0):
        midis = {}
        _matrix = matrix[0]
        col, row = _matrix.shape
        if offset_len <= 0 or offset_start + offset_len > col:
            offset_stop = col
        else:
            offset_stop = offset_start + offset_len
        for j in range(row):
            cnt = 0
            offset = -1
            for i in range(offset_start, offset_stop):
                if _matrix[i][j] == 3:
                    cnt += 1
                    if offset < 0:
                        offset = i
                elif _matrix[i][j] == 2:
                    cnt += 1
                    midi = j + self.key_start
                    if offset not in midis:
                        midis[offset] = [[midi, cnt]]
                    else:
                        midis[offset] += [[midi, cnt]]
                    cnt = 0
                    offset = -1
        return midis

    def convert_matrix(self, data):
        _len = int(data['total_len'])
        matrix = np.zeros([1, _len, self.key_range], dtype=np.int8)
        notes = data['noteset']
        for n in notes:
            self.fill_note(n, matrix)
        return matrix

    def analysis(self, data):
        staff = {}
        staff['key'] = data['info']['key']
        staff['title'] = data['info']['title']
        staff['composer'] = data['info']['composer']
        staff['tempo'] = data['info']['tempo']
        staff['timesign'] = data['info']['timesign']
        staff['tracks'] = data['tracks']
        playtracks = {}
        full_matrix = np.zeros([1, 1, 0], dtype=np.int8)
        for k, v in data['playtracks'].items():
            al = Analysis(staff, v)
            _data = al.get_result()
            _data['instrument'] = staff['tracks'][k]
            if _data['noteset']:
                m = self.convert_matrix(_data)
                if not full_matrix.any():
                    full_matrix = m
                else:
                    full_matrix = np.append(full_matrix, m, axis=0)
                _data['matrix_index'] = full_matrix.shape[0] - 1
            playtracks[k] = _data
        staff['playtracks'] = playtracks
        self.full_matrix = full_matrix
        return staff

    def render(self, staff):
        for k, v in staff['playtracks'].items():
            total_len = int(v['total_len'])
            rns = v['roman_numerals']
            styles = v['styles']
            keys = v['keys']
            emotions = v['emotions']
            instructions = v['instructions']
            instrument = v['instrument']
            if instrument[-1] == 'B':
                handlers = self.beats_handlers
            elif instrument[-1] == 'M':
                handlers = self.melody_handlers
            elif instrument[-1] == 'R':
                handlers = self.rhythm_handlers
            else:
                raise ValueError
            i = 0
            callbacks = None
            input_matrix = np.zeros([total_len, self.key_range], dtype=np.int8)
            matrix_obj = Matrix(self.full_matrix, input_matrix)
            while i < total_len:
                # step1. check styles and load handler
                if i in styles:
                    style = styles[i]
                    callbacks = handlers[style]
                if callbacks:
                    if i in instructions:
                        callbacks.handle_instruction(
                            i, instructions[i], matrix_obj)
                    if i in keys:
                        callbacks.handle_key(i, keys[i], matrix_obj)
                    if i in emotions:
                        callbacks.handle_emotion(i, emotions[i], matrix_obj)
                    if i in rns:
                        callbacks.handle_rn(i, rns[i], matrix_obj)
                i += 1
                if input_matrix.any():
                    self.full_matrix = np.append(
                        self.full_matrix, input_matrix.reshape([1, total_len, self.key_range]))
                    v['matrix_index'] = self.full_matrix.shape[0] - 1
        return self.full_matrix


class RPC:
    def __init__(self):
        self.nodes = {}
        self.jack_master = jack.Client('jack_master')
        self.tbm = TimebaseMaster()
        self.tbm.activate()
        if not self.tbm.become_timebase_master():
            raise RuntimeError('time mater failed!')

    def close(self):
        self.jack_master.close()
        self.tbm.close()
        for n in self.nodes.values():
            n.close()

    def play(self, bpm=120):
        self.tbm.bpm = bpm
        self.tbm.transport_start()

    def pause(self):
        self.tbm.transport_stop()

    def stop(self):
        self.tbm.transport_stop()
        self.tbm.transport_locate(0)

    def get_all_ports(self):
        _ports = []
        ports = self.jack_master.get_ports()
        for port in ports:
            d = {'aliases': port.aliases, 'name': port.name,
                 'is_audio': port.is_audio, 'is_input': port.is_input,
                 'is_output': port.is_output, 'is_midi': port.is_midi,
                 'is_physical': port.is_physical, 'is_terminal': port.is_terminal}
            _ports.append(d)
        return _ports

    def _get_ports(self, ports):
        _ports = {}
        for port in ports:
            n, p = port.name.split(':')
            if n not in _ports:
                _ports[n] = {'input': [], 'output': []}
            if port.is_input:
                _ports[n]['input'].append(p)
            elif port.is_output:
                _ports[n]['output'].append(p)
        return _ports

    def get_midi_ports(self):
        ports = self.jack_master.get_ports(is_midi=True)
        return self._get_ports(ports)

    def get_audio_ports(self):
        ports = self.jack_master.get_ports(is_audio=True)
        return self._get_ports(ports)

    def get_ports_info(self, names):
        ports = []
        for n in names:
            ports.append(self.get_port_info)
        return ports

    def get_port_info(self, name):
        port = self.jack_master.get_port_by_name(name)
        d = {'aliases': port.aliases, 'name': port.name,
             'is_audio': port.is_audio, 'is_input': port.is_input,
             'is_output': port.is_output, 'is_midi': port.is_midi,
             'is_physical': port.is_physical, 'is_terminal': port.is_terminal}
        return d

    def _get_all_connections(self, port):
        l = self.jack_master.get_all_connections(port)
        return [p.name for p in l]

    def get_all_nodes(self):
        nodes = {}
        ports = self.jack_master.get_ports()
        for port in ports:
            conn = self._get_all_connections(port.name)
            node_name, port_name = port.name.split(':')
            if node_name not in nodes:
                nodes[node_name] = [
                    {'audio': [{'input': []}, {'output': []}]},
                    {'midi': [{'input': []}, {'output': []}]}]
            node = nodes[node_name]
            if port.is_audio:
                if port.is_input:
                    node[0]['audio'][0]['input'].append({port.shortname: conn})
                elif port.is_output:
                    node[0]['audio'][1]['output'].append({port.shortname: conn})
            elif port.is_midi:
                if port.is_input:
                    node[1]['midi'][0]['input'].append({port.shortname: conn})
                elif port.is_output:
                    node[1]['midi'][1]['output'].append({port.shortname: conn})
            _nodes = []
            for k, v in nodes.items():
                _nodes.append({k: v})
        return _nodes

    def add_synth(self, name):
        if name in self.nodes:
            return False
        synth = Synth(name, self.jack_master.samplerate)
        self.nodes[name] = synth
        return True

    def del_synth(self, name):
        if name not in self.nodes:
            return False
        synth = self.nodes[name]
        synth.close()
        del self.nodes[name]

    def add_seq(self, name):
        if name in self.nodes:
            return False
        seq = Sequencer(name)
        self.nodes[name] = seq
        return True

    def del_seq(self, name):
        if name not in self.nodes:
            return False
        seq = self.nodes[name]
        seq.close()
        del self.nodes[name]

    def load_midi(self, name, data):
        if not isinstance(data, xmlrpc.client.Binary):
            return False
        if name not in self.nodes:
            return False
        fp = tempfile.TemporaryFile()
        fp.write(data.data)
        fp.seek(0)
        mid = MidiFile(file=fp)
        node = self.nodes[name]
        node.load_midi(mid)
        fp.close()
        return True

    def load_audio(self, data):
        if not isinstance(data, xmlrpc.client.Binary):
            return False
        fp = tempfile.TemporaryFile()
        fp.write(data.data)
        fp.seek(0)
        fp.close()
        return True

    def connect(self, src, dst):
        self.jack_master.connect(src, dst)

    def disconnect(self, src, dst):
        self.jack_master.disconnect(src, dst)

    def disconnect_all(self, src):
        ports = self.jack_master.get_all_connections(src)
        for p in ports:
            self.jack_master.disconnect(p, src)

    def get_params(self, params):
        pass

    def set_params(self, params):
        pass


def demo01():
    cb = CoderBand()
    data = cb.parse(sys.argv[1])
    full_matrix = cb.render(data)
    mid = Midi(data, full_matrix)
    data = mid.data()
    data.save('main.mid')


def demo02():
    rpc = RPC()
    # mid.save('main.mid')
    print("Press <Ctrl+C> to exit...")
    try:
        with SimpleXMLRPCServer(('localhost', 8000),
                                allow_none=True, requestHandler=RequestHandler) as server:
            server.register_introspection_functions()
            server.register_multicall_functions()
            server.register_instance(rpc)
            # Run the server's main loop
            server.serve_forever()
    except KeyboardInterrupt:
        rpc.close()
        print("Exit!")


if __name__ == '__main__':
    demo02()
