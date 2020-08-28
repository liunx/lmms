#!/usr/bin/env python3

from music21 import *
import sys


class ChordState(tinyNotation.State):
    def affectTokenAfterParse(self, n):
        super(ChordState, self).affectTokenAfterParse(n)
        return None  # do not append Note object

    def end(self):
        ch = chord.Chord(self.affectedTokens)
        ch.duration = self.affectedTokens[0].duration
        return ch

def info(notation):
    tnc = tinyNotation.Converter(notation)
    tnc.bracketStateMapping['chord'] = ChordState
    s = tnc.parse().stream
    _len = len(s)
    print("Measures: {}".format(_len))


if __name__ == "__main__":
    info(sys.argv[1])
