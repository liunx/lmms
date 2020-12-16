import os
import sys
from mcore import MCore
from common import Note
from parameters import NoteLen, Percussion

rock = [
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
    [1, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0]]

dance = [
    [0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0],
    [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
    [1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0]]

group01 = [
    Percussion.ClosedHiHat,
    Percussion.AcousticSnare,
    Percussion.AcousticBassDrum]

group02 = [
    Percussion.ClosedHiHat,
    Percussion.HandClap,
    Percussion.BassDrum1]

group03 = [
    Percussion.ClosedHiHat,
    Percussion.SideStick,
    Percussion.BassDrum1]

staff = {
    'key': 'C',
    'tempo': '90',
    'timesign': '4/4',
    'tracks': {'beat': [
        'beat',
        'Percussion',
        '0',
        'F']},
    'playtracks': {
        'beat': {
            'noteset': [],
            'styles': [],
            'roman_numerals': [],
            'emotions': [],
            'instructions': [],
            'total_len': 0}}}

cbd_beat = {
    'info': {
        'key': 'C',
        'title': 'Beats Templates',
        'name': 'Beats Templates',
        'composer': 'CoderBand',
        'tempo': '90',
        'style': 'rock',
        'timesign': '4/4'},
    'tracks': {
        'beat': [
            'beat',
            'Percussion',
            '0',
            'F']},
    'clips': {},
    'playtracks': {
        'beat': ['c1']}}


class Beats(Note):
    matrix_len = 16
    instruments = group01
    beats_pattern = rock

    def __init__(self, staff={}):
        self.staff = staff
        ts = self.staff['timesign']
        self.matrix_len = self.matrix_length_table[ts]

    def algorithm01(self, b=0, m=0, h=0):
        _m = self.beats_pattern.copy()
        high = _m[0]
        middle = _m[1]
        bass = _m[2]
        if h > 0 and h < self.matrix_len:
            for i in range(0, self.matrix_len, h):
                high[i] = 1
        if m > 0 and m < self.matrix_len:
            for i in range(0, self.matrix_len, m):
                middle[i] = 1
        if b > 0 and b < self.matrix_len:
            for i in range(0, self.matrix_len, b):
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
            noteset += self.matrix_to_noteset(beats,
                                              NoteLen._1st * (i + self.offset))
        self.offset += times

    def process(self):
        self.offset = 0
        playtracks = self.staff['playtracks']
        tracks = self.staff['tracks']
        for k, v in playtracks.items():
            if tracks[k][1] == 'Percussion':
                noteset = []
                self.generate_noteset(noteset, 2)
                self.generate_noteset(noteset, 4, b=5, h=2)

                self.beats_pattern = dance
                self.instruments = group03
                self.generate_noteset(noteset, 2)
                self.generate_noteset(noteset, 4, b=3)

                v['noteset'] = noteset


class Render(Note):
    def __init__(self, staff, init_data={}):
        self.staff = staff
        self.init_data = init_data

    def process(self, cbd):
        self.segment_roman_numerals(self.staff)
        beats = Beats(self.staff)
        beats.process()
        self.update_cbd_playtracks(self.staff, cbd)


def demo(fp):
    data = cbd_beat.copy()
    render = Render(staff)
    render.process(data)
    mcore = MCore()
    mcore.cbd(data)
    mcore.writecbd(fp)


if __name__ == '__main__':

    init_data = {}
    fp = sys.argv[1]
    demo(fp)
