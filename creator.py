from common import Note
import pprint
from fractions import Fraction
import music21 as m21
from parameters import *
pp = pprint.PrettyPrinter(indent=4)


class Rhythm(Note):
    def __init__(self, staff):
        self.staff = staff
        self.time_line = {}

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

    def m21_roman(self, note):
        key = self.staff['key']
        rn = note['roman_numeral']
        rf = m21.roman.RomanNumeral(rn, key)
        rf.transpose('-P8', inPlace=True)
        return rf

    def add_note(self, midi, length, offset):
        n = {}
        n['midi'] = midi
        n['len'] = length
        n['offset'] = offset
        return n

    def add_chord(self, midis, length, offset):
        chord = []
        for midi in midis:
            chord.append(self.add_note(midi, length, offset))
        return chord

    def add_quarter_rhythm(self, note):
        notes = []
        midis = []
        time_sign = note['timesign']
        rf = self.m21_roman(note)
        if rf.isTriad():
            root = rf.root().midi
            third = rf.third.midi
            fifth = rf.fifth.midi
            midis = [root, third, fifth, root + 12]
        elif rf.isSeventh():
            pass
        else:
            raise ValueError(
                'Unsupported chord type: {}!'.format(note['roman_numeral']))
        len_ = NOTE_LEN_4TH
        offset_ = note['offset']
        notes += self.add_chord(midis, len_, offset_)
        return notes

    def broken_chord(self, midis, len_, offset):
        notes = []
        for midi in midis:
            notes.append(self.add_note(midi, len_, offset))
            offset += len_
        return notes

    def add_half_rhythm(self, note):
        offset_ = note['offset']
        rf = self.m21_roman(note)
        if not (rf.isTriad() or rf.isSeventh()):
            raise ValueError(
                'Unsupported chord type: {}!'.format(note['roman_numeral']))
        root = rf.root().midi
        third = rf.third.midi
        fifth = rf.fifth.midi
        midis = [root, third, fifth]
        seventh = rf.seventh
        if seventh:
            midis.append(seventh.midi)
        else:
            midis.append(root + 12)
        return self.broken_chord(midis, NOTE_LEN_8TH, offset_)

    def add_third_rhythm(self, note):
        notes = []
        return notes

    def add_whole_rhythm(self, note):
        offset_ = note['offset']
        rf = self.m21_roman(note)
        if not (rf.isTriad() or rf.isSeventh()):
            raise ValueError(
                'Unsupported chord type: {}!'.format(note['roman_numeral']))
        root = rf.root().midi
        third = rf.third.midi
        fifth = rf.fifth.midi
        seventh = rf.seventh
        if seventh:
            seventh = seventh.midi
            midis = [root, third, fifth, seventh,
                     root + 12, seventh, fifth, third]
        else:
            midis = [root, third, fifth, root + 12,
                     third + 12, root + 12, fifth, third]
        return self.broken_chord(midis, NOTE_LEN_8TH, offset_)

    def add_rhythm(self, note):
        notes = []
        meter = note['meter']
        if meter == '1/4':
            notes = self.add_quarter_rhythm(note)
        elif meter == '1/2':
            notes = self.add_half_rhythm(note)
        elif meter == '3/4':
            notes = self.add_third_rhythm(note)
        elif meter == '1':
            notes = self.add_whole_rhythm(note)
        else:
            raise ValueError('Unsupported meter: {}!'.format(meter))
        return notes

    def expand_roman_numerals(self, roman_numerals):
        notes = []
        for rn in roman_numerals:
            self.time_measure(rn)
            notes += self.add_rhythm(rn)
        return notes

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
            noteset_ = []
            notes = self.expand_roman_numerals(rns)
            if v['noteset']:
                noteset_.append(v['noteset'])
                noteset_.append(notes)
            else:
                noteset_ = notes
            v['noteset'] = noteset_


class Melody:
    def __init__(self, staff):
        self.staff = staff
        pass

    def process(self):
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

    def add_note(self, midi, len_, offset):
        n = {}
        n['midi'] = midi
        n['len'] = len_
        n['offset'] = offset
        return n

    def _add_beats(self, midi, beats, len_, offset):
        notes = []
        for b in beats:
            if b > 0:
                notes.append(self.add_note(midi, len_, offset))
            offset += len_
        return notes

    def add_whole_beats(self, rn):
        notes = []
        bass = Percussion.BassDrum1
        middle = Percussion.SideStick
        high = Percussion.ClosedHiHat
        bass_beats = [1, 0, 0, 0, 1, 0, 0, 0]
        notes += self._add_beats(bass, bass_beats, NoteLen._8th, rn['offset'])
        middle_beats = [0, 0, 1, 0, 0, 0, 1, 0]
        notes += self._add_beats(middle, middle_beats,
                                 NoteLen._8th, rn['offset'])
        high_beats = [1, 1, 1, 1, 1, 1, 1, 1]
        notes += self._add_beats(high, high_beats, NoteLen._8th, rn['offset'])
        return notes

    def add_half_beats(self, rn):
        pass

    def add_third_beats(self, rn):
        pass

    def add_quarter_beats(self, rn):
        pass

    def add_beats(self, rn):
        notes = []
        meter = rn['meter']
        if meter == '1':
            notes = self.add_whole_beats(rn)
        elif meter == '1/2':
            notes = self.add_half_beats(rn)
        elif meter == '3/4':
            notes = self.add_third_beats(rn)
        elif meter == '1/4':
            notes = self.add_quarter_beats(rn)
        else:
            raise ValueError('Unsupported meter: {}!'.format(meter))
        return notes

    def expand_roman_numerals(self, roman_numerals):
        notes = []
        for rn in roman_numerals:
            self.time_measure(rn)
            notes += self.add_beats(rn)
        return notes

    def process(self):
        playtracks = self.staff['playtracks']
        tracks = self.staff['tracks']
        for k, v in playtracks.items():
            track = tracks[k]
            # ignore percussion
            if track[1] == 'Percussion':
                rns = v['roman_numerals']
                if rns:
                    notes = self.expand_roman_numerals(rns)
                    noteset_ = []
                    print(v['emotions'])
                    if v['noteset']:
                        noteset_.append(v['noteset'])
                        noteset_.append(notes)
                    else:
                        noteset_ = notes
                    v['noteset'] = noteset_
