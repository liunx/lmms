# the mcore.py
import os
import sys
import json
import re
from lmms import Lmms
from fractions import Fraction
from  parameters import Param
from common import Note
from music21 import stream, chord, tinyNotation, instrument, \
    converter, meter, note, metadata


class Struct:
    def __init__(self, **args):
        self.__dict__.update(args)


class ChordState(tinyNotation.State):
    def affectTokenAfterParse(self, n):
        super(ChordState, self).affectTokenAfterParse(n)
        return None  # do not append Note object

    def end(self):
        ch = chord.Chord(self.affectedTokens)
        ch.duration = self.affectedTokens[0].duration
        return ch


class MCore(Note):
    instruments = {}
    track2notes = {}
    lmms_beatsbaselines = 1
    def __init__(self, data):
        realpath = os.path.realpath(sys.argv[0])
        self.init_data = data
        self.basedir = os.path.dirname(realpath)
        self.instruments = self.json_load(self.basedir + '/data/generic_midi.json')
        self.percussion = self.collect_percussion()

    def cbd(self, cbd):
        self.info = cbd['info']
        self.tracks = cbd['tracks']
        self.playbacks = cbd['playbacks']
        # convert to stream
        staff = stream.Score()
        md = metadata.Metadata()
        md.composer = self.info['composer']
        md.title = self.info['title']
        staff.append(md)
        ts = self.info['timesign']
        timesign = meter.TimeSignature(ts)
        staff.append(timesign)
        # name, instrument, pitch, muted
        title = 'tinyNotation: {} '.format(ts) 
        for k, v in self.tracks.items():
            if v[3] == 'T':
                continue
            notes = self.playbacks[k]
            notation = self._notation(notes)
            part = self.tinynote(title + notation)
            self.track2notes[k] = part
            pitch = int(v[2])
            if pitch:
                part.transpose(pitch, inPlace=True)
            inst = self._instrument(v[1])
            part.insert(0, inst)
            staff.append(part)
        self.staff = staff

    def _instrument(self, name):
        if name not in self.instruments:
            print("Error: instrument {} not found!".format(name))
            sys.exit(1)
        inst = self.instruments[name]
        _inst = instrument.Instrument()
        _inst.instrumentName = inst[0]
        _inst.midiChannel = inst[1]
        _inst.midiProgram = inst[2]
        _inst.lowestNote = inst[3]
        _inst.highestNote = inst[4]
        return _inst

    def _notation(self, notes):
        notation = ''
        for n in notes:
            if type(n) is list:
                n = n[0] + '{' + ' '.join(n[1:]) + '}'
            notation +=  n + ' '
        return notation

    def tinynote(self, notation):
        tnc = tinyNotation.Converter(notation)
        tnc.bracketStateMapping['chord'] = ChordState
        return tnc.parse().stream

    def xml(self, fp):
        self.staff = converter.parse(fp)

    def midi(self, fp):
        self.staff = converter.parse(fp)

    def writemidi(self, fp):
        self.staff.write('midi', fp=fp)

    def writexml(self, fp):
        self.staff.write('musicxml', fp=fp)

    def to_note(self, n):
        _note = ''
        octave = n.octave
        name = n.step
        alter = n.pitch.alter
        ql = n.quarterLength
        if ql == 0:
            return _note
        # name convert
        if octave < 4:
            count = 4 - octave
            _note = name.upper() * count
        elif octave == 4:
            _note = name.lower()
        elif octave > 4:
            count = octave - 4
            _note = name.lower()
            _note = _note[0] + "'" * count + _note[1:]
        if alter > 0:
            _note += '#' * int(alter)
        elif alter < 0:
            _note += '-' * abs(int(alter))
        # length
        _len = self.notation_length_map[n.duration.type]
        _note = f'{_note}{_len}'
        # dots
        _note = f'{_note}' + '.' * n.duration.dots
        try:
            if n.tie.type in ['start', 'continue']:
                _note += '~'
        except AttributeError:
            pass
        return _note

    def _tinynote(self, note, note_len):
        note_name = re.sub('\d+.*', '', note)
        notes1, left_len1 = self.quarter_notes(note_name, note_len)
        if left_len1 == 0:
            return notes1
        notes2, left_len2 = self.quarter_notes(note_name, note_len)
        if left_len2 == 0:
            return notes2
        raise ValueError('Can not handle the note: {}!'.format(note_name))

    def divide_note(self, note, current_len, left_len):
        if left_len == 0:
            return note, None
        new_len = current_len - left_len
        if note.startswith('r'):
            l_note = self.fill_rests(new_len)
            r_note = self.fill_rests(left_len)
        else:
            l_note = self._tinynote(note, new_len)
            r_note = self._tinynote(note, left_len)
            l_note[-1] = '{}~'.format(l_note[-1])
            if note.endswith('~'):
                r_note[-1] = '{}~'.format(r_note[-1])
        return l_note, r_note

    def divide_chord(self, chord, current_len, left_len):
        if left_len == 0:
            return chord, None
        new_len = current_len - left_len
        l_chord = ['chord']
        r_chord = ['chord']
        for note in chord:
            l_note = self._tinynote(note, new_len)
            r_note = self._tinynote(note, left_len)
            l_note[-1] = '{}~'.format(l_note[-1])
            if note.endswith('~'):
                r_note[-1] = '{}~'.format(r_note[-1])
            l_chord += l_note
            r_chord += r_note
        return l_chord, r_chord

    def divide_bars(self, track, bar_len):
        l = []
        ll = []
        offset = 0
        _track = track.copy()
        while True:
            if len(_track) == 0:
                if ll:
                    l.append(ll)
                break
            note = _track.pop(0)
            if type(note) == list:
                if note[0] == 'chord':
                    note_len = self.note_len(note[-1])
                    offset += note_len
                    if offset == bar_len:
                        ll.append(note)
                        l.append(ll)
                        offset = 0
                        ll = []
                    elif offset > bar_len:
                        l_chord, r_chord = self.divide_chord(note[1:], note_len, offset - bar_len)
                        ll += [l_chord]
                        l.append(ll)
                        offset = 0
                        ll = []
                        if r_chord:
                            _track = [r_chord] + _track
                    else:
                        ll.append(note)
                elif note[0] == 'trip':
                    _track = note[1:] + _track
                    continue
            else:
                note_len = self.note_len(note)
                offset += note_len
                if offset == bar_len:
                    ll.append(note)
                    l.append(ll)
                    offset = 0
                    ll = []
                elif offset > bar_len:
                    l_note, r_note = self.divide_note(note, note_len, offset - bar_len)
                    ll += l_note
                    l.append(ll)
                    ll = []
                    offset = 0
                    if r_note:
                        _track = r_note + _track
                else:
                    ll.append(note)
        return l

    def format_playbacks(self, indent):
        l = []
        bar_len = self.bar_length_table[self.info['timesign']]
        _playbacks = {}
        for k, v in self.playbacks.items():
            bars = self.divide_bars(v, bar_len)
            _playbacks[k] = bars
        keys = list(_playbacks.keys())
        i = 0
        while True:
            ll = []
            for k in keys:
                bars = _playbacks[k]
                if len(bars) > i:
                    bars = bars[i:i+indent]
                    if not bars:
                        continue
                    s = '{}-> ['.format(k)
                    _first = 1
                    for bar in bars:
                        if _first:
                            _first = 0
                        else:
                            s += ' |'
                        for n in bar:
                            if type(n) == list:
                                if n[0] == 'chord':
                                    ss = ' chord{'
                                    for nn in n[1:]:
                                        ss += ' {}'.format(nn)
                                    ss += ' }'
                                    s += ss
                                elif n[0] == 'trip':
                                    ss = ' trip{'
                                    for nn in n[1:]:
                                        ss += ' {}'.format(nn)
                                    ss += ' }'
                                    s += ss
                            else:
                                s += ' {}'.format(n)
                    s += ' ]\n'
                    ll.append(s)
            if not ll:
                # remove last '--'
                l.pop(-1)
                break
            l += ll
            l.append('--\n')
            i += indent

        return l

    def writecbd(self, fp, indent=4):
        lines = []
        lines.append('@Generated by Coderband!!!\n')
        lines.append('title: "{}"\n'.format(self.info['title']))
        lines.append('composer: "{}"\n'.format(self.info['composer']))
        lines.append('tempo: {}\n'.format(self.info['tempo']))
        lines.append('timesign: {}\n'.format(self.info['timesign']))
        lines.append('key: "{}"\n'.format(self.info['key']))
        lines.append('\n')
        lines.append('@Instruments\n')
        for k, v in self.tracks.items():
            lines.append('{}: ({}, {}, {}, {})\n'.format(k, v[0], v[1], v[2], v[3]))
        lines.append('\n')
        # measure count
        offset = 1
        lines.append('@Playbacks\n')
        lines.append('>>\n')
        lines += self.format_playbacks(indent)
        lines.append('<<\n')
        # write to file
        with open(fp, 'w') as f:
            f.writelines(lines)

    def pianoroll(self, part):
        roll = []
        for m in  part:
            if type(m) != stream.Measure:
                continue
            for n in m:
                d = {}
                if type(n) == note.Note:
                    d = {'type': 'Note', 'key': n.pitch.midi, 'pos': float(n.offset), 'len': float(n.quarterLength)}
                elif type(n) == chord.Chord:
                    d = {'type': 'Chord', 'keys': [p.midi for p in n.pitches], 'pos': float(n.offset), 'len': float(n.quarterLength)}
                if d:
                    roll.append(d)
            roll.append({'type': 'Measure'})
        return roll

    def json_load(self, fp):
        d = {}
        with open(fp) as f:
            d = json.load(f)
        return d

    def json_store(self, fp, data):
        with open(fp, 'w') as f:
            json.dump(data, fp)

    def flatten(self, l, a):
        for i in l:
            if isinstance(i, list):
                self.flatten(i, a)
            else:
                a.append(i)
        return a

    def collect_percussion(self):
        d = {}
        for k, v in self.instruments.items():
            if k == 'Percussion':
                continue
            # midi channel 10
            if v[1] == 10:
                prog = v[2] + 1
                d[prog] = k
        return d

    def add_beatspattern(self, patterns, beats):
        for p in patterns:
            pn = p.attrib['name']
            for b in beats:
                bn = self.percussion.get(b[0])
                if pn == bn:
                    self.lmms.addbeatnote(p, b[1])

    def add_beatsbaselines(self, part):
        baselines = {}
        mi = 0
        for m in  part:
            if type(m) != stream.Measure:
                continue
            notes = []
            beats = []
            for n in m:
                if type(n) == note.Note:
                    notes.append('{}{}'.format(n.nameWithOctave, n.quarterLength))
                    beats.append([n.pitch.midi, n.offset])
                elif type(n) == chord.Chord:
                    for i in n.notes:
                        notes.append('{}{}'.format(i.nameWithOctave, i.quarterLength))
                        beats.append([i.pitch.midi, n.offset])
            bl = ''.join(notes)
            if bl not in baselines:
                track, patterns = self.lmms.addbeatbaseline('Beat/Bassline {}'.format(self.lmms_beatsbaselines))
                baselines[bl] = track
                self.lmms_beatsbaselines += 1
                self.add_beatspattern(patterns, beats)
                self.lmms.addbbtco(track, mi, 1)
            else:
                track = baselines[bl]
                self.lmms.addbbtco(track, mi, 1)
            mi += 1

    def _add_beats_instrument(self, name):
        inst = self.lmms_instruments.get(name)
        if not inst:
            print("Error: Instrument {} not found!".format(name))
            sys.exit(1)
        inst = Struct(**inst)
        inst.name = name
        inst.preset = self.basedir + '/' + inst.preset
        attrib = self.lmms.addinstrument(inst)

    def add_beats_instruments(self, part):
        drumkit = []
        for m in  part:
            if type(m) != stream.Measure:
                continue
            for n in m:
                if type(n) == note.Note:
                    if n.pitch.midi in drumkit:
                        continue
                    inst_name = self.percussion[n.pitch.midi]
                    self._add_beats_instrument(inst_name)
                    drumkit.append(n.pitch.midi)
                elif type(n) == chord.Chord:
                    for i in n.notes:
                        if i.pitch.midi in drumkit:
                            continue
                        inst_name = self.percussion[i.pitch.midi]
                        self._add_beats_instrument(inst_name)
                        drumkit.append(i.pitch.midi)

    def add_beats(self, trackname):
        part = self.track2notes.get(trackname)
        self.add_beats_instruments(part)
        self.add_beatsbaselines(part)

    def writelmms(self, fp):
        proj = '/data/projects/templates/default.mpt'
        self.lmms_instruments = self.json_load(self.basedir + '/data/lmms.json')
        self.lmms = Lmms(self.basedir + proj)
        self.lmms.changebpm(self.info['tempo'])
        for k, v in self.tracks.items():
            if v[1] == 'Percussion':
                self.add_beats(k)
                continue
            inst = self.lmms_instruments.get(v[1])
            if not inst:
                print("Error: Instrument {} not found!".format(v[1]))
                sys.exit(1)
            inst['name'] = v[0]
            inst = Struct(**inst)
            inst.preset = self.basedir + '/' + inst.preset
            node = self.lmms.addinstrument(inst)
            part = self.track2notes.get(k)
            notes = self.pianoroll(part)
            self.lmms.addnotes(node['pattern'], notes, 0, 0, 100)
        self.lmms.write(fp)

    def show_percussion(self):
        for k, v in self.instruments.items():
            if k == 'Percussion':
                continue
            # midi channel 10
            if v[1] == 10:
                prog = v[2]
                n = note.Note(prog + 1)
                n1 = self.to_note(n)
                n1 = n1.replace('4', '')
                print('{}: {}'.format(k, n1))