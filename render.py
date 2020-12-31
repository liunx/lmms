import os
import sys
import numpy as np
from mcore import MCore
from common import Note
from parameters import NoteLen, Percussion
import parameters as param
import algorithm as alg
import models
import pkgutil
import importlib
import mods.beats


class Beats(Note):
    instruments = models.group01
    beats_pattern = models.rock

    def __init__(self, staff):
        self.offset = 0
        self.style_history = []
        self.emotion_history = []
        self.instruction_history = []
        self.handlers = {}
        self.staff = staff
        for m in pkgutil.iter_modules(mods.beats.__path__):
            l = importlib.import_module('mods.beats.' + m.name)
            self.handlers[m.name] = l.callback

    def algorithm01(self, b=0, m=0, h=0):
        _m = self.beats_pattern.copy()
        _m_len = len(_m[0])
        high = _m[0]
        middle = _m[1]
        bass = _m[2]
        if h > 0 and h < _m_len:
            for i in range(0, _m_len, h):
                high[i] = 1
        if m > 0 and m < _m_len:
            for i in range(0, _m_len, m):
                middle[i] = 1
        if b > 0 and b < _m_len:
            for i in range(0, _m_len, b):
                bass[i] = 1
        return _m

    def matrix_to_noteset(self, matrix, abs_offset=0):
        noteset = []
        w = len(matrix[0])
        h = len(matrix)
        unit_size = NoteLen._1st // w
        for i in range(h):
            for j in range(w):
                if matrix[i][j] > 0:
                    _note = {'midi': self.instruments[i]}
                    _note['offset'] = j * unit_size + abs_offset
                    _note['len'] = unit_size
                    noteset.append(_note)
        return noteset

    def generate_noteset(self, noteset, times, b=0, m=0, h=0):
        for i in range(times):
            beats = self.algorithm01(b, m, h)
            noteset += self.matrix_to_noteset(beats, self.offset)
            self.offset += NoteLen._1st

    def matrix_to_noteset2(self, matrix, instruments, offset, len_):
        noteset = []
        w = len(matrix[0])
        h = len(matrix)
        unit_size = len_ // w
        for i in range(h):
            for j in range(w):
                if matrix[i][j] > 0:
                    _note = {'midi': instruments[i]}
                    _note['offset'] = j * unit_size + offset
                    _note['len'] = unit_size
                    noteset.append(_note)
        return noteset

    def process(self):
        self.offset = 0
        playtracks = self.staff['playtracks']
        tracks = self.staff['tracks']
        for k, v in playtracks.items():
            if tracks[k][1] == 'Percussion':
                noteset = []
                self.generate_noteset(noteset, 2)
                self.generate_noteset(noteset, 2, h=3)
                self.beats_pattern = models.triple01
                self.generate_noteset(noteset, 2)
                self.generate_noteset(noteset, 2, h=3)
                self.generate_noteset(noteset, 2, b=2, h=1)
                self.beats_pattern = models.dance
                self.generate_noteset(noteset, 2)
                self.generate_noteset(noteset, 2, h=3)
                self.generate_noteset(noteset, 2, b=2, h=1)
                v['noteset'] = noteset

    def render(self, rn):
        style = rn['style']
        callback = self.handlers[style]
        beats, instruments = callback(rn)
        return self.matrix_to_noteset2(beats, instruments, rn['offset'], rn['len'])


class Rhythm(Note):
    base_midi = 48
    scales = 25

    def __init__(self, staff):
        self.staff = staff

    def matrix_to_noteset(self, matrix, abs_offset=0):
        noteset = []
        w = len(matrix[0])
        h = len(matrix)
        unit_size = NoteLen._1st // w
        for i in range(h):
            row = matrix[i]
            j = 0
            _count = 0
            _midi = self.base_midi + i
            while j < w:
                if matrix[i][j] == 0:
                    j += 1
                    continue
                if matrix[i][j] == 0b10:
                    _note = {'midi': _midi}
                    _note['offset'] = j * unit_size + abs_offset
                    _note['len'] = (_count + 1) * unit_size
                    noteset.append(_note)
                    _count = 0
                elif matrix[i][j] == 0b11:
                    _note = {'midi': _midi}
                    _note['offset'] = j * unit_size + abs_offset
                    while j < w:
                        if matrix[i][j] == 0:
                            _note['len'] = _count * unit_size
                            noteset.append(_note)
                            _count = 0
                            break
                        elif matrix[i][j] == 0b10:
                            _note['len'] = (_count + 1) * unit_size
                            noteset.append(_note)
                            _count = 0
                            break
                        _count += 1
                        j += 1
                    if _count > 0:
                        _note['len'] = _count * unit_size
                        noteset.append(_note)
                        _count = 0
                j += 1

        return noteset

    def matrix_to_noteset2(self, matrix, offset, len_):
        noteset = []
        w = len(matrix[0])
        h = len(matrix)
        unit_size = len_ // w
        for i in range(h):
            row = matrix[i]
            j = 0
            _count = 0
            _midi = self.base_midi + i
            while j < w:
                if matrix[i][j] == 0:
                    j += 1
                    continue
                if matrix[i][j] == 0b10:
                    _note = {'midi': _midi}
                    _note['offset'] = j * unit_size + offset
                    _note['len'] = (_count + 1) * unit_size
                    noteset.append(_note)
                    _count = 0
                elif matrix[i][j] == 0b11:
                    _note = {'midi': _midi}
                    _note['offset'] = j * unit_size + offset
                    while j < w:
                        if matrix[i][j] == 0:
                            _note['len'] = _count * unit_size
                            noteset.append(_note)
                            _count = 0
                            break
                        elif matrix[i][j] == 0b10:
                            _note['len'] = (_count + 1) * unit_size
                            noteset.append(_note)
                            _count = 0
                            break
                        _count += 1
                        j += 1
                    if _count > 0:
                        _note['len'] = _count * unit_size
                        noteset.append(_note)
                        _count = 0
                j += 1

        return noteset

    def is_overlap(self, note_a, note_b):
        a = (note_a['offset'], note_a['offset'] + note_a['len'])
        b = (note_b['offset'], note_b['offset'] + note_b['len'])
        if a == b:
            return False
        return a[1] > b[0] and b[1] > a[0]

    def bubble_sort(self, noteset):
        for i in range(len(noteset) - 1):
            for j in range(len(noteset) - i - 1):
                if noteset[j]['offset'] > noteset[j+1]['offset']:
                    noteset[j], noteset[j+1] = noteset[j+1], noteset[j]
        return noteset

    def arrange_noteset(self, noteset):
        _noteset = self.bubble_sort(noteset)
        overlaps = []
        non_overlaps = []
        current_noteset = _noteset
        ll = []
        while True:
            for note in current_noteset:
                if not non_overlaps:
                    non_overlaps.append(note)
                    continue
                if self.is_overlap(note, non_overlaps[-1]):
                    overlaps.append(note)
                else:
                    non_overlaps.append(note)
            if overlaps:
                current_noteset = overlaps.copy()
                ll.append(non_overlaps.copy())
                non_overlaps = []
                overlaps = []
                continue
            else:
                ll.append(non_overlaps.copy())
                break
        return ll

    def generate_noteset(self, noteset, matrix, times):
        for i in range(times):
            noteset += self.matrix_to_noteset(matrix, self.offset)
            self.offset += NoteLen._1st

    def generate_matrix(self, matrix, vectors):
        w = len(matrix[0])
        m = [[0] * w] * self.scales
        i = 0
        for v in vectors:
            m[v] = matrix[i]
            i += 1
        return np.array(m)

    def demo01(self):
        noteset = []
        vectors = [0, 4, 7, 12, 16]
        table = np.array([4, 4, 4, 4])
        table = alg.fragment(table, 4 * 1, 4, 4 * 0)
        m1 = alg.wave_sine(table, len(vectors))
        m2 = alg.wave_saw(table, len(vectors))
        m = m1 | m2
        matrix = self.generate_matrix(m, vectors)
        self.generate_noteset(noteset, matrix, 4)
        _noteset = self.arrange_noteset(noteset)
        return _noteset

    def demo02(self):
        noteset = []
        vectors = [0, 4, 7, 12, 16]
        tables = alg.table_demo01(np.array([2, 2, 2, 2, 2, 2, 2, 2]))
        i = 0
        for table in tables:
            table = np.array(table)
            m = alg.wave_saw(table, len(vectors))
            matrix = self.generate_matrix(m, vectors)
            self.generate_noteset(noteset, matrix, 1)
            self.base_midi = 48 + vectors[i % 4]
            i += 1
        _noteset = self.arrange_noteset(noteset)
        return _noteset

    def demo03(self):
        noteset = []
        vectors = [0, ]
        tables = alg.table_demo02(np.array([3, 1, 2, 2]))
        self.base_midi = 36 + 7
        for table in tables:
            table = np.array(table)
            m = alg.wave_sawi(table, len(vectors))
            matrix = self.generate_matrix(m, vectors)
            self.generate_noteset(noteset, matrix, 2)
        _noteset = self.arrange_noteset(noteset)
        return _noteset

    def render(self, rn):
        table = np.array([1, 1, 1, 1, 1, 1, 1, 1])
        if rn['len'] < NoteLen._1st:
            table = np.split(table, NoteLen._1st // rn['len'])[0]
        vectors = [0, 4, 7, 12]
        _key = param.modes[rn['key'].upper()]
        _rn = param.roman_numerals[rn['roman_numeral'].upper()]
        self.base_midi = _key + _rn
        m = alg.wave_sawi(table, len(vectors))
        matrix = self.generate_matrix(m, vectors)
        return self.matrix_to_noteset2(matrix, rn['offset'], rn['len'])

    def process(self):
        self.offset = 0
        playtracks = self.staff['playtracks']
        tracks = self.staff['tracks']
        for k, v in playtracks.items():
            if tracks[k][1] == 'EFBass':
                _noteset = self.demo03()
                v['noteset'] = _noteset


class Render(Note):
    def __init__(self, init_data={}):
        self.init_data = init_data

    def render_beats(self, staff, cbd):
        self.segment_roman_numerals(staff)
        beats = Beats(staff)
        beats.process()
        self.update_cbd_playtracks(staff, cbd)

    def render_rhythm(self, staff, cbd):
        self.segment_roman_numerals(staff)
        rhythm = Rhythm(staff)
        rhythm.process()
        self.update_cbd_playtracks(staff, cbd)


def demo_beats(fp):
    cbd = models.cbd_beats.copy()
    staff = models.staff_beats.copy()
    render = Render()
    render.render_beats(staff, cbd)
    mcore = MCore()
    mcore.cbd(cbd)
    mcore.writecbd(fp)


def demo_rhythm(fp):
    cbd = models.cbd_rhythm.copy()
    staff = models.staff_rhythm.copy()
    render = Render()
    render.render_rhythm(staff, cbd)
    mcore = MCore()
    mcore.cbd(cbd)
    mcore.writecbd(fp)


if __name__ == '__main__':

    init_data = {}
    fp = sys.argv[1]
    demo_rhythm(fp)
