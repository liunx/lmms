import re
from parameters import Param


class Note(Param):

    def note_len(self, note, triple=False):
        """ Convert length of tinynote to generic note length. """
        num = 0
        dot = 0
        m = re.match(r'([a-grA-GR\'#-]+)(\d+)([.]*)', note)
        if not m:
            raise ValueError("Unknown note: {}!".format(note))
        num = int(m.group(2))
        dots = m.group(3).count('.')
        _len = self.whole_length / num
        current_len = _len
        for _ in range(dots):
            _len += current_len / 2
            current_len = current_len / 2
        if triple:
            _len = _len * 2 / 3
        if not _len.is_integer():
            raise ValueError("Can not handle the note: {}!".format(note))
        return _len

    def get_tinynote_len(self, note_len):
        """ Convert generic note length to tinynote length """
        result = []
        l = [192, 128, 96, 64, 48, 32, 24, 16, 12, 8, 6, 4, 3]
        n = ['1', 'trip1', '2', 'trip2', '4', 'trip4', '8',
             'trip8', '16', 'trip16', '32', 'trip32', '64']
        current_len = note_len
        for _len, _name in zip(l, n):
            quotient = int(current_len // _len)
            reminder = int(current_len % _len)
            if quotient > 0:
                result += [_name] * quotient
            current_len = reminder
            if reminder == 0:
                break
        if current_len > 0:
            raise ValueError("Can not handle note length: {}".format(note_len))

        return result

    def tinynote_with_len(self, name, note_len):
        """ Generate tinynote with given name and length """
        notes = []
        lens = self.get_tinynote_len(note_len)
        for l in lens:
            if l.startswith('trip'):
                l = l.replace('trip', '')
                notes.append(f'trip{{ {name}{l}~ }}')
            else:
                notes.append(f'{name}{l}~')
        notes[-1] = notes[-1].replace('~', '')
        return notes

    def _rests_divide(self, lens, names, note_len):
        rests = []
        current_len = note_len
        for _len, name in zip(lens, names):
            quotient = int(current_len // _len)
            reminder = int(current_len % _len)
            if quotient > 0:
                rests += [name] * quotient
            current_len = reminder
            if reminder == 0:
                break
        return rests, current_len

    def quarter_rests(self, note_len):
        rests = []
        l = [192, 96, 48, 24, 12, 6, 3]
        n = ['r1', 'r2', 'r4', 'r8', 'r16', 'r32', 'r64']
        return self._rests_divide(l, n, note_len)

    def triple_rests(self, note_len):
        rests = []
        l = [128, 64, 32, 16, 8, 4]
        n = [['trip', 'r1'], ['trip', 'r2'], ['trip', 'r4'],
             ['trip', 'r8'], ['trip', 'r16'], ['trip', 'r32']]
        return self.rests_divide(l, n, note_len)

    def fill_rests(self, note_len):
        # prefer quarter rests
        quarter_rests, left_len1 = self.quarter_rests(note_len)
        if left_len1 == 0:
            return quarter_rests
        triple_rests, left_len2 = self.triple_rests(note_len)
        if left_len2 == 0:
            return triple_rests
        triple_rests, left_len2 = self.triple_rests(left_len1)
        if left_len2 > 0:
            raise ValueError(
                'Can handle with the length of {}!'.format(note_len))
        return quarter_rests + triple_rests

    def midi_to_note_name(self, midi):
        note_names = ['c', 'c#', 'd', 'd#', 'e',
                      'f', 'f#', 'g', 'g#', 'a', 'a#', 'b']
        note_name = 'c'
        idx = midi % 12
        n = note_names[idx]
        if midi >= 60:
            alter = (midi - 60) // 12
            note_name = n[0] + "'" * alter + n[1:]
        else:
            alter = (60 - midi) // 12
            if alter > 0:
                note_name = n[0].upper() * alter + n[1:]
            else:
                note_name = n[0].upper() + n[1:]
        return note_name

    def quarter_notes(self, note_name, note_len):
        l = [192, 96, 48, 24, 12, 6, 3]
        n = [1, 2, 4, 8, 16, 32, 64]
        notes = []
        current_len = note_len
        for _len, _type in zip(l, n):
            quotient = int(current_len // _len)
            reminder = int(current_len % _len)
            if reminder > 0:
                if quotient > 0:
                    for i in range(quotient):
                        notes.append(f'{note_name}{_type}~')
            elif reminder == 0:
                current_len = 0
                if quotient > 0:
                    for i in range(quotient):
                        notes.append(f'{note_name}{_type}~')
                    # strip out last ~
                    notes[-1] = notes[-1].replace('~', '')
                break
            current_len = reminder
        return notes, current_len

    def triple_notes(self, note_name, note_len):
        l = [128, 64, 32, 16, 8, 4]
        n = [1, 2, 4, 8, 16, 32]
        notes = []
        current_len = note_len
        for _len, _type in zip(l, n):
            quotient = int(current_len // _len)
            reminder = int(current_len % _len)
            if reminder > 0:
                if quotient > 0:
                    for i in range(quotient):
                        notes.append(['trip', f'{note_name}{_type}~'])
            elif reminder == 0:
                current_len = 0
                if quotient > 0:
                    for i in range(quotient):
                        notes.append(['trip', f'{note_name}{_type}~'])
                    # strip out last ~
                    notes[-1] = notes[-1].replace('~', '')
                break
            current_len = reminder
        return notes, current_len

    def to_tinynote(self, note):
        note_len = note['len']
        note_name = self.midi_to_note_name(note['midi'])
        notes1, left_len1 = self.quarter_notes(note_name, note_len)
        if left_len1 == 0:
            return notes1
        notes2, left_len2 = self.quarter_notes(note_name, note_len)
        if left_len2 == 0:
            return notes2
        raise ValueError('Can not handle the note: {}!'.format(note_name))


if __name__ == "__main__":
    note = Note()
    l = note.tinynote_with_len('C#', 192 + 192)
    print(l)
