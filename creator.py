from common import Note
from fractions import Fraction
import music21 as m21
from parameters import *
import render


class Rhythm(Note):
    def __init__(self, staff):
        self.staff = staff

    def time_measure(self, note):
        timesign = note['timesign']
        meter_len = note['meter_len']
        _len = int(note['len'])
        _offset = note['offset']
        start_pos = int(_offset % meter_len)
        stop_pos = int((_offset + _len) % meter_len)
        f_start = '0'
        f_stop = '0'
        if start_pos > 0:
            f_start = Fraction(start_pos, meter_len)
        if stop_pos > 0:
            f_stop = Fraction(stop_pos, meter_len)
        note['start'] = str(f_start)
        note['stop'] = str(f_stop)
        f_meter = Fraction(_len, meter_len)
        note['meter'] = str(f_meter)

    def expand_roman_numerals(self, roman_numerals):
        notes = []
        rhythm = render.Rhythm(self.staff)
        for rn in roman_numerals:
            self.time_measure(rn)
            notes += rhythm.render(rn)
        return notes

    def process(self):
        playtracks = self.staff['playtracks']
        tracks = self.staff['tracks']
        for k, v in playtracks.items():
            track = tracks[k]
            if track[4] == 'R':
                rns = v['roman_numerals']
                if not rns:
                    continue
                v['noteset'] = self.expand_roman_numerals(rns)


class Melody:
    def __init__(self, staff):
        self.staff = staff
        pass

    def process(self):
        playtracks = self.staff['playtracks']
        tracks = self.staff['tracks']
        for k, v in playtracks.items():
            track = tracks[k]
            if track[4] == 'M':
                pass


class Beats:
    def __init__(self, staff):
        self.staff = staff

    def time_measure(self, rn):
        timesign = rn['timesign']
        meter_len = rn['meter_len']
        _len = int(rn['len'])
        _offset = rn['offset']
        start_pos = int(_offset % meter_len)
        stop_pos = int((_offset + _len) % meter_len)
        f_start = '0'
        f_stop = '0'
        if start_pos > 0:
            f_start = Fraction(start_pos, meter_len)
        if stop_pos > 0:
            f_stop = Fraction(stop_pos, meter_len)
        rn['start'] = str(f_start)
        rn['stop'] = str(f_stop)
        f_meter = Fraction(_len, meter_len)
        rn['meter'] = str(f_meter)

    def expand_roman_numerals(self, roman_numerals):
        noteset = []
        beats = render.Beats(self.staff)
        for rn in roman_numerals:
            self.time_measure(rn)
            noteset += beats.render(rn)
        return noteset

    def process(self):
        playtracks = self.staff['playtracks']
        tracks = self.staff['tracks']
        for k, v in playtracks.items():
            track = tracks[k]
            if track[4] == 'B':
                rns = v['roman_numerals']
                if not rns:
                    continue
                v['noteset'] = self.expand_roman_numerals(rns)
