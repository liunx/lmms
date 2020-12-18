#!/usr/bin/env python3

import subprocess
import argparse
import os
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


class TripChordState(tinyNotation.State):
    def affectTokenAfterParse(self, n):
        super(TripChordState, self).affectTokenAfterParse(n)
        return None  # do not append Note object

    def end(self):
        ch = chord.Chord(self.affectedTokens)
        ch.duration = duration.Duration(
            self.affectedTokens[0].duration.quarterLength * 2 / 3)
        return ch


class KeyToken(tinyNotation.Token):
    def parse(self, parent):
        keyName = self.token
        print(keyName)
        return note.Note(keyName)


class Notation:
    def __init__(self, args):
        notation = ''
        if args.file:
            with open(args.file) as f:
                notation = 'tinyNotation: 4/4 ' + f.read()
        elif args.notation:
            notation = f'tinyNotation: 4/4 {args.notation}'
        else:
            notation = 'tinyNotation: 4/4 ' + sys.stdin.read()
        tnc = tinyNotation.Converter(notation)
        tnc.bracketStateMapping['chord'] = ChordState
        tnc.bracketStateMapping['tripchord'] = TripChordState
        keyMapping = (r'trip-(.*)', KeyToken)
        tnc.tokenMap.append(keyMapping)
        self.staff = tnc.parse().stream
        if args.drumkit:
            inst = instrument.Percussion()
        else:
            inst = instrument.Instrument()
            inst.midiProgram = args.program
        self.staff.insert(0, inst)
        self.args = args

    def play(self):
        midfile = '/tmp/{}.mid'.format(str(id('midi')))
        self.staff.write('midi', fp=midfile)
        subprocess.run(
            ['timidity', '--quiet=2',
             f'-A{self.args.vol}',
             f'-T {self.args.tempo}',
             f'-K {self.args.pitch}',
             f'-Ei{self.args.program}',
             midfile])
        os.remove(midfile)

    def show(self):
        self.staff.show('text')


def addargs():
    parser = argparse.ArgumentParser(description='arguments ArgumentParser.')
    parser.add_argument('-t', '--tempo', default=120, type=int)
    parser.add_argument('-v', '--vol', default=200, type=int)
    parser.add_argument('-p', '--pitch', default=0, type=int)
    parser.add_argument('-P', '--program', default=0, type=int)
    parser.add_argument('-d', '--drumkit', default=False, action='store_true')
    parser.add_argument('-f', '--file', type=str)
    parser.add_argument('notation', type=str, nargs='?',
                        help="if None, read from stdin")
    args = parser.parse_args()
    return args


if __name__ == '__main__':
    args = addargs()
    n = Notation(args)
    n.show()
