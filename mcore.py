# the mcore.py
import os
import sys
import json
from music21 import stream, chord, tinyNotation, instrument


class ChordState(tinyNotation.State):
    def affectTokenAfterParse(self, n):
        super(ChordState, self).affectTokenAfterParse(n)
        return None  # do not append Note object

    def end(self):
        ch = chord.Chord(self.affectedTokens)
        ch.duration = self.affectedTokens[0].duration
        return ch


class MCore:
    instruments = {}
    def __init__(self, cbd):
        info = cbd['info']
        tracks = cbd['tracks']
        playbacks = cbd['playbacks']
        root = os.path.dirname(sys.argv[0])
        with open(root + '/data/generic_midi.json') as f:
            self.instruments = json.load(f)
        # convert to stream
        staff = stream.Stream()
        ts = info['timesign']
        # name, instrument, pitch, muted
        title = 'tinyNotation: {} '.format(ts) 
        for k, v in tracks.items():
            if v[3] == 'T':
                continue
            notes = playbacks[k]
            notation = self._notation(notes)
            part = self.tinynote(title + notation)
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

    def writemidi(self, fp):
        self.staff.write('midi', fp=fp)