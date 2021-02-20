import sys
import pkgutil
import importlib
import numpy as np
from parser import MyLexer
from analysis import Analysis
import mods.beats
import mods.rhythm
import mods.melody


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


if __name__ == '__main__':
    cb = CoderBand()
    data = cb.parse(sys.argv[1])
    cb.render(data)
