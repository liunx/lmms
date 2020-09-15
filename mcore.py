# the mcore.py
import os
import sys
import json
from lmms import Lmms
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


class MCore:
    time_signature_map = {
        '4/4': 'r1',
        '3/4': 'r2.',
        '2/4': 'r2',
        '3/8': 'r4.',
        '6/8': 'r2.',
    }

    notation_length_map = {
        'whole': 1,
        'half': 2,
        'quarter': 4,
        'eighth': 8,
        '16th': 16,
        '32nd': 32,
    }
    instruments = {}
    track2notes = {}
    def __init__(self):
        realpath = os.path.realpath(sys.argv[0])
        self.basedir = os.path.dirname(realpath)

    def cbd(self, cbd):
        self.info = cbd['info']
        self.tracks = cbd['tracks']
        self.playbacks = cbd['playbacks']
        with open(self.basedir + '/data/generic_midi.json') as f:
            self.instruments = json.load(f)
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
        name = n.name
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

    def to_rest(self, n):
        ql = n.quarterLength
        if ql == 0:
            return ''
        _note = 'r'
        # length
        _len = self.notation_length_map[n.duration.type]
        _note = f'{_note}{_len}'
        # dots
        _note = f'{_note}' + '.' * n.duration.dots
        return _note

    def addnotation(self, m):
        s = ""
        for n in m:
            if type(n) == chord.Chord:
                s = s + 'chord{ '
                for nt in n.notes:
                    ns = self.to_note(nt)
                    print(ns)
                    s = s + f'{ns} '
                s = s + '} '
            elif type(n) == note.Note:
                ns = self.to_note(n)
                s = s + f'{ns} '
            elif type(n) == note.Rest:
                ns = self.to_rest(n)
                s = s + f'{ns} '
            else:
                # TODO
                pass
        return s

    def addmeasures(self, stream_, count, offset):
        l = []
        i = 1
        for p in stream_.parts:
            if not p.measure(offset):
                continue
            s = 'track{:02}-> [ '.format(i)
            for n in range(count):
                m = p.measure(offset + n)
                if not m:
                    r = self.time_signature_map[self.ts]
                    s = s + f'{r} '
                else:
                    nt = self.addnotation(m)
                    s = s + nt
                if n == count - 1:
                    s = s + ']'
                else:
                    s = s + '| '
            if s[-1] != ']':
                print(s)
            l.append(s)
            l.append('\n')
            i = i + 1
        _offset = offset + count
        return _offset, l

    def writecbd(self, fp, step=4):
        lines = []
        if not self.instruments:
            self.instruments = self.json_load(self.basedir + '/data/generic_midi.json')
        lines.append('@Generated by Coderband!!!\n')
        for md in self.staff.getElementsByClass('Metadata'):
            lines.append(f'title: "{md.title}"\n')
            lines.append(f'composer: "{md.composer}"\n')
            lines.append('tempo: 120\n')
            break
        for t in self.staff.recurse().getElementsByClass(meter.TimeSignature):
            lines.append(f'timesign: {t.ratioString}\n')
            self.ts = t.ratioString
            break
        lines.append('\n')
        for i in range(len(self.staff.parts)):
            p = self.staff.parts[i]
            inst = p.getInstrument()
            if inst.instrumentName:
                prog = inst.midiProgram
                keys = list(self.instruments.keys())
                instname = keys[prog]
                lines.append('track{:02}: (melody{:02}, {}, 0, F)\n'.format(i + 1, i + 1, instname))
            else:
                lines.append('track{:02}: (melody{:02}, APiano, 0, F)\n'.format(i + 1, i + 1))
        lines.append('\n')
        # measure count
        offset = 1
        lines.append('>>\n')
        mcount = len(self.staff.parts[0].measureOffsetMap())
        div = mcount // step
        for i in range(div):
            offset, l = self.addmeasures(self.staff, step, offset)
            if i < (div - 1):
                l.append('--\n')
            lines = lines + l
        dmod = mcount % step
        if dmod > 0:
            _, l = self.addmeasures(self.staff, dmod, offset)
            lines = lines + l
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

    def writelmms(self, fp):
        proj = '/data/projects/templates/default.mpt'
        instruments = self.json_load(self.basedir + '/data/lmms.json')
        lmms = Lmms(self.basedir + proj)
        lmms.changebpm(self.info['tempo'])
        for k, v in self.tracks.items():
            inst = instruments.get(v[1])
            if not inst:
                print("Error: Instrument {} not found!".format(v[1]))
                sys.exit(1)
            inst['name'] = v[0]
            inst = Struct(**inst)
            inst.preset = self.basedir + '/' + inst.preset
            node = lmms.addinstrument(inst)
            part = self.track2notes.get(k)
            notes = self.pianoroll(part)
            lmms.addnotes(node['pattern'], notes, 0, 0, 100)
        lmms.write(fp)