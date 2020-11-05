import re
import copy
from operator import itemgetter
import music21 as m21


class Core:
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

    def __init__(self, data):
        self.noteset = []
        self.roman_numerals = []
        self.instructions = []
        self.styles = []
        self.emotions = []
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
        n1 = 48 / num
        curr = n1
        for _ in range(dot):
            n1 += curr / 2
            curr = curr / 2
        return n1

    def to_note(self, note, offset):
        d = {}
        d['offset'] = offset
        midi = self.note_midi(note)
        d['pitch'] = midi
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
            self.instructions.append(d)
        elif n.startswith('$$'):
            d = {'offset': offset, 'style': n[2:]}
            self.styles.append(d)
        elif n.startswith('!'):
            d = {'offset': offset, 'roman_numeral': n[1:]}
            self.roman_numerals.append(d)
        elif n.startswith('*'):
            d = {'offset': offset, 'emotion': n[1:]}
            self.emotions.append(d)
        else:
            print("[Err]: Unknown keyword {}!".format(n))

    def to_noteset(self, data):
        offset = 0
        i = 0
        for n in data:
            # chord | trip
            if type(n) == list:
                if n[0] == 'chord':
                    n.pop(0)
                    _len = self.note_len(n[0])
                    for _n in n:
                        d = self.to_note(_n, offset)
                        d['len'] = _len
                        self.noteset.append(d)
                    offset += _len
                elif n[0] == 'trip':
                    n.pop(0)
                    _len = self.note_len(n[0]) * 2 / 3
                    for _n in n:
                        d = self.to_note(_n, offset)
                        d['len'] = _len
                        self.noteset.append(d)
                        offset += _len
                else:
                    print("[Err]: Unknown keyword! {}".format(n[0]))
            else:
                # skip keywords
                if not self.is_note(n):
                    self.divide_keyword(n, offset)
                    continue
                # skip Rest note
                if n[0].upper() == 'R':
                    offset += self.note_len(n)
                    continue
                d = self.to_note(n, offset)
                _len = self.note_len(n)
                offset += _len
                d['len'] = _len
                self.noteset.append(d)

    def _tie(self, nset, i):
        _len = len(self.noteset)
        while i < _len:
            _nset = self.noteset[i]
            if _nset['pitch'] == nset['pitch'] and (nset['offset'] + nset['len']) == _nset['offset']:
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


class Beats(Core):
    def __init__(self, data):
        super().__init__(data)

    def update_percussion(self):
        for i in self.noteset:
            if i['pitch'] not in self.percussion:
                print(
                    "[Err]: No matched percussion instrument for pitch {}!".format(i['pitch']))
                continue
            inst = self.percussion[i['pitch']]
            i['instrument'] = inst
            if inst in ['AcousticBassDrum', 'BassDrum1']:
                i['freq'] = 'Bass'
            elif inst in ['SideStick', 'AcousticSnare']:
                i['freq'] = 'Middle'
            elif inst in ['OpenHi-Hat', 'ClosedHiHat']:
                i['freq'] = 'High'
            else:
                print(
                    "[Err]: Unknown percussion instrument {} for freq!".format(inst))

    def analysis(self, data):
        self.to_noteset(data)
        self.update_percussion()


class Melody(Core):
    def __init__(self, data):
        super().__init__(data)

    def update_melody(self):
        # get the total length of notesets
        if not self.noteset:
            return
        n = self.noteset[-1]
        total_len = n['offset'] + n['len']
        _len = len(self.roman_numerals)
        i = 0
        while i < _len:
            rn = self.roman_numerals[i]
            if rn['roman_numeral'] == 'N':
                rn['drop'] = 1
                continue
            if (i + 1) == _len:
                rn['len'] = total_len - rn['offset']
                break
            _rn = self.roman_numerals[i + 1]
            rn['len'] = _rn['offset'] - rn['offset']
            i += 1

    def analysis(self, data):
        self.to_noteset(data)
        self.update_tie()
        self.update_melody()


class Rhythm(Core):
    def __init__(self, data):
        super().__init__(data)

    def update_rhythm(self):
        pitches = []
        inversions = {}
        for i in self.noteset:
            pitches.append(i['pitch'])
        _chord = m21.chord.Chord(pitches)
        if _chord.isTriad():
            inversions[_chord.root().name] = '1st'
            inversions[_chord.third.name] = '3rd'
            inversions[_chord.fifth.name] = '5th'
        elif _chord.isSeventh():
            inversions[_chord.root().name] = '1st'
            inversions[_chord.third.name] = '3rd'
            inversions[_chord.fifth.name] = '5th'
            inversions[_chord.seventh.name] = '7th'
        else:
            print("[Err]: Unknown chord {}".format(_chord.fullName))
            return
        min_pitch = min(pitches)
        for i in self.noteset:
            n = m21.note.Note(i['pitch'])
            i['inversion'] = inversions[n.name]
            i['pitch'] -= min_pitch

    def analysis(self, data):
        self.to_noteset(data)
        self.update_tie()
        self.update_rhythm()


if __name__ == "__main__":
    data = ['C4~', ['chord', 'E4~', 'G4~'], [
        'chord', 'E4~', 'G4~'], ['chord', 'E4', 'G4']]
    data2 = ['C4', ['trip', 'C4', 'E4', 'G4']]
    data3 = ['C4~', 'C4', 'E4~', 'E4']
    data4 = ['CC8', 'r8', 'DD8', 'CC8', 'CC8', 'r8', 'DD8', 'r8']
    data5 = [
        'c2', '!up', '!good', 'c4.', 'c8', 'c2', '!happy', 'c2', 'c1~', 'c1', 'G2', 'c4.', 'c8', 'c1', 'G2', 'd4.',
        'B8', 'c1', 'G2', 'c4.', 'e8', 'g2', 'e4', 'c4', 'd2', 'c4.', 'd8', 'd1', 'G2', 'c4.',
        'c8', 'c1', 'G2', 'd4.', 'B8', 'c1', 'G2', 'c4.', 'e8', 'g2', 'e4', 'c4', 'f2', 'e4.',
        'd8', 'c1', 'r1', 'r1', 'r1', 'r1']
    data6 = ['!I', 'R1', '!II', 'R1', '!III', '!IV', '!V', '!VI', '!VII']
    data7 = ['$$pop', 'r1', '!I', 'r1', '*happy', '!IV', '!V7', '!i', '!Isus4', '!!ts_44', '!!to_D']
    #rym = Rhythm(data)
    #bt = Beats(data4)
    ml = Melody(data7)
    # ml.show_noteset()
