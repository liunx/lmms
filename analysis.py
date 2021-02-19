import re
import copy
from operator import itemgetter
import music21 as m21


class Core:
    meter_len = 192
    notes = {'C': 60, 'D': 62, 'E': 64, 'F': 65, 'G': 67, 'A': 69, 'B': 71}
    percussion = {
        35: 'AcousticBassDrum', 36: 'BassDrum1', 37: 'SideStick', 38: 'AcousticSnare',
        39: 'HandClap', 40: 'ElectricSnare', 41: 'LowFloorTom', 42: 'ClosedHiHat',
        43: 'HighFloorTom', 44: 'PedalHi-Hat', 45: 'LowTom', 46: 'OpenHi-Hat',
        47: 'Low-MidTom', 48: 'Hi-MidTom', 49: 'CrashCymbal1', 50: 'HighTom',
        51: 'RideCymbal1', 52: 'ChineseCymbal', 53: 'RideBell', 54: 'Tambourine',
        55: 'SplashCymbal', 56: 'Cowbell', 57: 'CrashCymbal2', 58: 'Vibraslap',
        59: 'RideCymbal2', 60: 'HiBongo', 61: 'LowBongo', 62: 'MuteHiConga',
        63: 'OpenHiConga', 64: 'LowConga', 65: 'HighTimbale', 66: 'LowTimbale',
        67: 'HighAgogo', 68: 'LowAgogo', 69: 'Cabasa', 70: 'Maracas', 71: 'ShortWhistle',
        72: 'LongWhistle', 73: 'ShortGuiro', 74: 'LongGuiro', 75: 'Claves', 76: 'HiWoodBlock',
        77: 'LowWoodBlock', 78: 'MuteCuica', 79: 'OpenCuica', 80: 'MuteTriangle', 81: 'OpenTriangle'}

    def __init__(self, staff, data):
        self.total_len = 0
        self.noteset = []
        self.roman_numerals = []
        self.instructions = {}
        self.styles = {}
        self.emotions = {}
        self.time_signs = {0: staff['timesign']}
        self.keys = {0: staff['key']}
        self.analysis(copy.deepcopy(data))

    def show_noteset(self):
        print("==== total notes ====")
        for i in self.noteset:
            print(i)

    def note_midi(self, note):
        step = note[0].upper()
        midi = self.notes[step]
        if note[0].islower():
            midi += 12 * note.count("'")
        else:
            midi -= 12 * note.count(step)
        if note.count('-') > 0:
            alter = note.count('-')
            midi -= alter
        elif note.count('#') > 0:
            alter = note.count('#')
            midi += alter
        return midi

    def note_len(self, note):
        num = 0
        dot = 0
        # Rest & Notation
        m = re.match(r'([a-grA-GR\'#-]+)(\d+)([.]*)', note)
        if not m:
            return 0
        num = int(m.group(2))
        dot = m.group(3).count('.')
        n1 = self.meter_len / num
        curr = n1
        for _ in range(dot):
            n1 += curr / 2
            curr = curr / 2
        return n1

    def to_note(self, note, offset):
        d = {}
        d['offset'] = offset
        midi = self.note_midi(note)
        d['midi'] = midi
        if note.count('~') > 0:
            d['tie'] = 1
        else:
            d['tie'] = 0
        return d

    def is_note(self, note):
        m = re.match(r'[a-grA-GR\'#-]+\d+', note)
        if not m:
            return False
        return True

    def divide_keyword(self, n, offset):
        if n.startswith('!!'):
            d = {'offset': offset, 'instruction': n[2:]}
            self.instructions[offset] = n[2:]
        elif n.startswith('$$'):
            self.styles[offset] = n[2:]
        elif n.startswith('!'):
            d = {'offset': offset, 'roman_numeral': n[1:]}
            self.roman_numerals.append(d)
        elif n.startswith('*'):
            self.emotions[offset] = n[1:]
        else:
            raise ValueError("Unknown keyword: {}!".format(n))

    def to_noteset(self, data):
        offset = 0
        _len = 0
        for n in data:
            # chord | trip
            if type(n) == list:
                if n[0] == 'chord':
                    _len = self.note_len(n[-1])
                    for _n in n[1:]:
                        d = self.to_note(_n, offset)
                        d['len'] = _len
                        self.noteset.append(d)
                    offset += _len
                elif n[0] == 'tripchord':
                    _len = self.note_len(n[-1]) * 2 / 3
                    for _n in n[1:]:
                        d = self.to_note(_n, offset)
                        d['len'] = _len
                        self.noteset.append(d)
                    offset += _len
                elif n[0] == 'trip':
                    _len = self.note_len(n[-1]) * 2 / 3
                    for _n in n[1:]:
                        if _n[0] != 'r':
                            d = self.to_note(_n, offset)
                            d['len'] = _len
                            self.noteset.append(d)
                        offset += _len
                else:
                    raise ValueError("Unknown keyword: {}!".format(n[0]))
            else:
                # skip keywords
                if not self.is_note(n):
                    self.divide_keyword(n, offset)
                    continue
                # skip Rest note
                if n[0].upper() == 'R':
                    _len = self.note_len(n)
                    offset += _len
                    continue
                d = self.to_note(n, offset)
                _len = self.note_len(n)
                offset += _len
                d['len'] = _len
                self.noteset.append(d)
        self.total_len = offset

    def _tie(self, nset, i):
        _len = len(self.noteset)
        while i < _len:
            _nset = self.noteset[i]
            if _nset['midi'] == nset['midi'] and (nset['offset'] + nset['len']) == _nset['offset']:
                if _nset['tie'] > 0:
                    self._tie(_nset, i)
                    nset['tie'] = 0
                    nset['len'] += _nset['len']
                    _nset['drop'] = 1
                else:
                    nset['tie'] = 0
                    nset['len'] += _nset['len']
                    _nset['drop'] = 1
                    break
            i += 1

    def update_tie(self):
        _noteset = []
        _noteset_len = len(self.noteset)
        i = 0
        while i < _noteset_len:
            nset = self.noteset[i]
            if nset.get('drop'):
                i += 1
                continue
            if nset['tie'] > 0:
                self._tie(nset, i)
            i += 1
        for i in self.noteset:
            if i.get('drop'):
                continue
            _noteset.append(i)
        self.noteset = _noteset

    def update_roman_numeral(self):
        # get the total length of notesets
        if not self.total_len > 0:
            return
        _len = len(self.roman_numerals)
        if _len == 0:
            return
        i = 0
        while i < _len:
            rn = self.roman_numerals[i]
            if rn['roman_numeral'] == 'N':
                rn['drop'] = 1
                i += 1
                continue
            if (i + 1) == _len:
                rn['len'] = self.total_len - rn['offset']
                break
            _rn = self.roman_numerals[i + 1]
            rn['len'] = _rn['offset'] - rn['offset']
            i += 1
        # rm dropped set
        l = []
        for i in self.roman_numerals:
            if 'drop' in i:
                continue
            l.append(i)
        self.roman_numerals = l

    def analysis(self, data):
        raise NotImplementedError


class Analysis(Core):
    def __init__(self, staff, data):
        super().__init__(staff, data)

    def reform_roman_numeral(self):
        d = {}
        for rn in self.roman_numerals:
            d[rn['offset']] = rn
        return d

    def analysis(self, data):
        self.to_noteset(data)
        self.update_tie()
        self.update_roman_numeral()

    def get_result(self):
        d = {}
        d['noteset'] = self.noteset
        d['styles'] = self.styles
        d['roman_numerals'] = self.reform_roman_numeral()
        d['emotions'] = self.emotions
        d['instructions'] = self.instructions
        d['total_len'] = self.total_len
        d['time_signs'] = self.time_signs
        d['keys'] = self.keys
        return d
