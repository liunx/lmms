import re
from parameters import Param


class Note(Param):

    def get_dimension(self, testlist, dim=0):
        if isinstance(testlist, list):
            if testlist == []:
                return dim
            dim = dim + 1
            dim = self.get_dimension(testlist[0], dim)
            return dim
        else:
            if dim == 0:
                return -1
            else:
                return dim

    def reform_noteset(self, noteset):
        d = {}
        key = 'offset'
        l = [i[key] for i in noteset]
        values = set(l)
        for v in values:
            ll = []
            for n in noteset:
                if n[key] == v:
                    ll.append(n)
            d[v] = ll
        return d

    def add_chord(self, notes):
        chord = ['chord']
        for l in notes[1:]:
            if type(l) == list:
                for n in l[1:]:
                    chord.append(n)
            else:
                chord.append(l)
        return chord

    def add_triple_chord(self, notes):
        tripchord = ['tripchord']
        for l in notes[1:]:
            if type(l) == list:
                for n in l[1:]:
                    tripchord.append(n)
            else:
                tripchord.append(l)
        return tripchord

    def to_tinynotes(self, noteset):
        l = []
        _noteset = self.reform_noteset(noteset)
        current_len = 0
        offsets = list(_noteset.keys())
        offsets.sort()
        for offset in offsets:
            notes = _noteset[offset]
            if offset > current_len:
                rest_len = offset - current_len
                rests = self.fill_rests(rest_len)
                l += rests
            if len(notes) > 1:
                ll = []
                type_ = 'chord'
                for n in notes:
                    note_ = self.to_tinynote(n)
                    if type(note_[0]) == list and note_[0][0] == 'trip':
                        type_ = 'tripchord'
                        ll.append(note_[0][1])
                    else:
                        ll += note_
                ll.insert(0, type_)
                l.append(ll)
                current_len = offset + n['len']
            else:
                l += self.to_tinynote(notes[0])
                current_len = offset + notes[0]['len']
        return l

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
        return self._rests_divide(l, n, note_len)

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
                if midi % 12 == 0:
                    note_name = n[0].upper() * alter + n[1:]
                else:
                    note_name = n[0].upper() * (alter + 1) + n[1:]
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
                    notes[-1][-1] = notes[-1][-1].replace('~', '')
                break
            current_len = reminder
        return notes, current_len

    def to_tinynote(self, note):
        note_len = note['len']
        note_name = self.midi_to_note_name(note['midi'])
        _notes, left_len = self.quarter_notes(note_name, note_len)
        if left_len == 0:
            return _notes
        _notes, left_len = self.triple_notes(note_name, note_len)
        if left_len == 0:
            return _notes
        raise ValueError('Can not handle the note: {}!'.format(note_name))

    def update_cbd_playtracks(self, staff, cbd):
        tracks = cbd['tracks']
        playtracks = cbd['playtracks']
        _tracks = tracks.copy()
        tracks.clear()
        playtracks.clear()
        for k, v in staff['playtracks'].items():
            noteset = v['noteset']
            if not noteset:
                continue
            dim = self.get_dimension(noteset)
            if dim <= 1:
                noteset = [noteset]
            for i in range(len(noteset)):
                track = _tracks[k].copy()
                key = f'{k}{i+1}'
                track[0] = key
                tracks[key] = track
                play_track = self.to_tinynotes(noteset[i])
                playtracks[key] = play_track

    def divide_roman_numeral(self, rn):
        rns = []
        start = int(rn['offset'])
        stop = int(rn['offset'] + rn['len'])
        meter = rn['meter_len']
        offsets = [start]
        for i in range(start + 1, stop):
            if i % meter == 0:
                offsets.append(i)
        offsets.append(stop)
        if len(offsets) == 2:
            return [rn]
        for i in range(len(offsets) - 1):
            offset1 = offsets[i]
            offset2 = offsets[i+1]
            _rn = rn.copy()
            _rn['offset'] = offset1
            _rn['len'] = offset2 - offset1
            rns.append(_rn)
            i += 1
        return rns

    def segment_roman_numerals(self, staff):
        playtracks = staff['playtracks']
        for k, v in playtracks.items():
            rns = v['roman_numerals']
            if not rns:
                continue
            ts = staff['timesign']
            _rns = []
            meter_len = self.bar_length_table[ts]
            for rn in rns:
                rn['timesign'] = ts
                rn['meter_len'] = meter_len
                _rns += self.divide_roman_numeral(rn)
            v['roman_numerals'] = _rns


if __name__ == "__main__":
    note = Note()
    l = note.tinynote_with_len('C#', 192 + 192)
    print(l)
