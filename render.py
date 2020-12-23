import os
import sys
import numpy as np
from mcore import MCore
from common import Note
from parameters import NoteLen, Percussion
import algorithm

rock = [
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
    [1, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0]]

dance = [
    [0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0],
    [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
    [1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0]]

pattern01 = [
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
    [1, 0, 1, 0, 0, 0, 0, 1, 1, 0, 1, 0, 0, 0, 0, 0]]

triple01 = [
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0],
    [1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0]]

group01 = [
    Percussion.ClosedHiHat,
    Percussion.AcousticSnare,
    Percussion.AcousticBassDrum]

group02 = [
    Percussion.ClosedHiHat,
    Percussion.HandClap,
    Percussion.BassDrum1]

group03 = [
    Percussion.PedalHiHat,
    Percussion.AcousticSnare,
    Percussion.BassDrum1]

staff_beats = {
    'key': 'C',
    'tempo': '90',
    'timesign': '4/4',
    'tracks': {'beats': [
        'beat',
        'Percussion',
        '0',
        'F']},
    'playtracks': {
        'beats': {
            'noteset': [],
            'styles': [],
            'roman_numerals': [],
            'emotions': [],
            'instructions': [],
            'total_len': 0}}}

cbd_beats = {
    'info': {
        'key': 'C',
        'title': 'Beats Templates',
        'name': 'Beats Templates',
        'composer': 'CoderBand',
        'tempo': '90',
        'style': 'rock',
        'timesign': '4/4'},
    'tracks': {
        'beats': [
            'beat',
            'Percussion',
            '0',
            'F']},
    'clips': {},
    'playtracks': {
        'beats': ['c1']}}

staff_rhythm = {
    'key': 'C',
    'tempo': '90',
    'timesign': '4/4',
    'tracks': {'rhythm': [
        'rhythm',
        'APiano',
        '0',
        'F']},
    'playtracks': {
        'rhythm': {
            'noteset': [],
            'styles': [],
            'roman_numerals': [],
            'emotions': [],
            'instructions': [],
            'total_len': 0}}}

cbd_rhythm = {
    'info': {
        'key': 'C',
        'title': 'Beats Templates',
        'name': 'Beats Templates',
        'composer': 'CoderBand',
        'tempo': '90',
        'style': 'rock',
        'timesign': '4/4'},
    'tracks': {
        'rhythm': [
            'rhythm',
            'APiano',
            '0',
            'F']},
    'clips': {},
    'playtracks': {
        'rhythm': ['c1']}}


class Beats(Note):
    instruments = group01
    beats_pattern = rock

    def __init__(self, staff):
        self.staff = staff

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

    def process(self):
        self.offset = 0
        playtracks = self.staff['playtracks']
        tracks = self.staff['tracks']
        for k, v in playtracks.items():
            if tracks[k][1] == 'Percussion':
                noteset = []
                self.generate_noteset(noteset, 2)
                self.generate_noteset(noteset, 2, h=3)
                self.beats_pattern = triple01
                self.generate_noteset(noteset, 2)
                self.generate_noteset(noteset, 2, h=3)
                self.generate_noteset(noteset, 2, b=2, h=1)
                self.beats_pattern = dance
                self.generate_noteset(noteset, 2)
                self.generate_noteset(noteset, 2, h=3)
                self.generate_noteset(noteset, 2, b=2, h=1)

                v['noteset'] = noteset


class Rhythm(Note):
    base_midi = 48

    def __init__(self, staff, pattern):
        self.staff = staff
        self.pattern = pattern

    def horizon_flip(self, matrix):
        return np.fliplr(matrix).tolist()

    def vertical_flip(self, matrix):
        return np.flipud(matrix).tolist()

    def roll(self, matrix, shift, axis=None):
        return np.roll(matrix, shift, axis)

    def zoom_out(self, matrix, times):
        matrix = [i * times for i in matrix]
        return matrix

    def algorithm(self, callback=zoom_out):
        matrix = self.pattern.copy()
        # return self.zoom_out(matrix, 2)
        return self.horizon_flip(matrix)

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

    def generate_matrix(self, h, w):
        return np.array([[0] * w] * h)

    def get_from_matrix(self, matrix, index=[]):
        m = []
        for i in index:
            m.append(matrix[i])
        return m

    def process(self):
        self.offset = 0
        playtracks = self.staff['playtracks']
        tracks = self.staff['tracks']
        for k, v in playtracks.items():
            if tracks[k][1] == 'APiano':
                noteset = []
                matrix = self.generate_matrix(25, 16)
                m = self.get_from_matrix(matrix, [0, 4, 7, 12])
                m = algorithm.sin(m, 1, 1)
                self.generate_noteset(noteset, matrix, 4)

                _noteset = self.arrange_noteset(noteset)
                v['noteset'] = _noteset


class Render(Note):
    def __init__(self, init_data={}):
        self.init_data = init_data

    def render_beats(self, staff, cbd):
        self.segment_roman_numerals(staff)
        beats = Beats(staff)
        beats.process()
        self.update_cbd_playtracks(staff, cbd)

    def render_rhythm(self, staff, cbd, pattern):
        self.segment_roman_numerals(staff)
        rhythm = Rhythm(staff, pattern)
        rhythm.process()
        self.update_cbd_playtracks(staff, cbd)


def demo_beats(fp):
    cbd = cbd_beats.copy()
    staff = staff_beats.copy()
    render = Render()
    render.render_beats(staff, cbd)
    mcore = MCore()
    mcore.cbd(cbd)
    mcore.writecbd(fp)


pattern1 = [[0] * 16] * 25
pattern1[0] = [3, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
pattern1[4] = [0, 0, 3, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 3]
pattern1[7] = [0, 0, 0, 0, 3, 3, 0, 0, 0, 0, 0, 0, 3, 3, 0, 0]
pattern1[12] = [0, 0, 0, 0, 0, 0, 3, 3, 0, 0, 3, 3, 0, 0, 0, 0]
pattern1[16] = [0, 0, 0, 0, 0, 0, 0, 0, 3, 3, 0, 0, 0, 0, 0, 0]

pattern2 = [[0] * 4] * 25
pattern2[0] = [3, 3, 3, 2]
pattern2[12] = [0, 2, 2, 2]
pattern2[16] = [0, 2, 2, 2]
pattern2[19] = [0, 2, 2, 2]


def demo_rhythm(fp):
    cbd = cbd_rhythm.copy()
    staff = staff_rhythm.copy()
    render = Render()
    render.render_rhythm(staff, cbd, pattern1)
    mcore = MCore()
    mcore.cbd(cbd)
    mcore.writecbd(fp)


if __name__ == '__main__':

    init_data = {}
    fp = sys.argv[1]
    demo_rhythm(fp)
