#!/usr/bin/env python3
import sys
from music21 import *




class ChordState(tinyNotation.State):
    def affectTokenAfterParse(self, n):
        super(ChordState, self).affectTokenAfterParse(n)
        return None  # do not append Note object

    def end(self):
        ch = chord.Chord(self.affectedTokens)
        ch.duration = self.affectedTokens[0].duration
        return ch


class Parser:
    def __init__(self, fp):
        f = open(fp, 'r')
        self.lines = f.readlines()
        f.close()

    def process(self):
        pass


class Converter:
    def __init__(self):
        pass