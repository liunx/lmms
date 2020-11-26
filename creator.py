from common import Note
import pprint
from fractions import Fraction
import music21 as m21
pp = pprint.PrettyPrinter(indent=4)


class Rhythm(Note):
    def __init__(self, staff):
        self.staff = staff
        self.time_line = {}

    def time_measure(self, note):
        timesign = note['timesign']
        meter_len = note['meter_len']
        _len = note['len']
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

    def add_rhythm(self, note):
        print(note)
        notes = []
        key = self.staff['key']
        rf = m21.roman.RomanNumeral(note['roman_numeral'], key)
        rf.transpose('-P8', inPlace=True)
        time_sign = note['timesign']
        if note['start'] == '1/4':
            pass
        elif note['start'] == '1/2':
            pass
        elif note['start'] == '3/4':
            pass
        return notes

    def expand_roman_numerals(self, roman_numerals):
        for rn in roman_numerals:
            self.time_measure(rn)
            self.add_rhythm(rn)

    def process(self):
        playtracks = self.staff['playtracks']
        tracks = self.staff['tracks']
        for k, v in playtracks.items():
            track = tracks[k]
            # ignore percussion
            if track[1] == 'Percussion':
                continue
            # handle for Roman Numerals
            rns = v['roman_numerals']
            if not rns:
                continue
            self.expand_roman_numerals(rns)


class Melody:
    def __init__(self, staff):
        self.staff = staff
        pass

    def process(self):
        pass


class Beats:
    def __init__(self, staff):
        self.staff = staff
        pass

    def process(self):
        pass
