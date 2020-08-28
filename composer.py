#!/usr/bin/env python3
from lmms import Lmms, Sf2Player
from music21 import *


class ChordState(tinyNotation.State):
    def affectTokenAfterParse(self, n):
        super(ChordState, self).affectTokenAfterParse(n)
        return None  # do not append Note object

    def end(self):
        ch = chord.Chord(self.affectedTokens)
        ch.duration = self.affectedTokens[0].duration
        return ch


class Composer:
    band = {}
    def __init__(self):
        pass

    def addrhythm(self, rhythm):
        pass

    def addmelody(self, melody):
        pass

    def tonotation(self, notation):
        tnc = tinyNotation.Converter(notation)
        tnc.bracketStateMapping['chord'] = ChordState
        s = tnc.parse().stream
        _len = len(s)
        return (_len, self.pianoroll(s))

    def addbaseline(self, baseline):
        pass

    def pianoroll(self, stream):
        roll = []
        for m in  stream:
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


if __name__ == "__main__":
    comp = Composer()
    tnc = tinyNotation.Converter('tinyNotation: 4/4 C4 D4 trip{E4 F4 G4} A4 B4 c4 chord{C4 E4 G4}')
    tnc.bracketStateMapping['chord'] = ChordState
    s = tnc.parse().stream
    roll = comp.pianoroll(s)
    print(roll)


