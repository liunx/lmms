#!/usr/bin/env python3

import argparse
import sys
from fractions import Fraction
from music21 import *

timeSignatureMap = {
    '4/4': 'r1',
    '3/4': 'r2.',
    '2/4': 'r2',
    '3/8': 'r4.',
}

quarterLengthMap = {
    'whole': 1,
    'half': 2,
    'quarter': 4,
    'eighth': 8,
    '16th': 16,
    '32nd': 32,
}


class CBConverter:
    def __init__(self):
        self.ts = '4/4'

    def notation(self, n):
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
        _len = quarterLengthMap[n.duration.type]
        _note = f'{_note}{_len}'
        # dots
        _note = f'{_note}' + '.' * n.duration.dots
        return _note

    def rest(self, n):
        ql = n.quarterLength
        if ql == 0:
            return ''
        _note = 'r'
        # length
        _len = quarterLengthMap[n.duration.type]
        _note = f'{_note}{_len}'
        # dots
        _note = f'{_note}' + '.' * n.duration.dots
        return _note

    def addnotation(self, m):
        s = ""
        for n in m:
            if type(n) == chord.Chord:
                s = s + 'chord{'
                for nt in n.notes:
                    ns = self.notation(nt)
                    s = s + f' {ns} '
                s = s + '} '
            elif type(n) == note.Note:
                ns = self.notation(n)
                s = s + f' {ns} '
            elif type(n) == note.Rest:
                ns = self.rest(n)
                s = s + f' {ns} '
            else:
                # TODO
                pass
        return s

    def addmeasures(self, s, count, offset):
        l = []
        i = 1
        l.append('>>\n')
        for p in s.parts:
            s = 'p{:02}-> | '.format(i)
            for n in range(count):
                m = p.measure(offset + n)
                nt = self.addnotation(m)
                if nt != '':
                    s = s + nt
                else:
                    r = timeSignatureMap[self.ts]
                    s = s + r
                s = s + ' | '
            l.append(s)
            l.append('\n')
            i = i + 1
        _offset = offset + count

        return _offset, l

    def process(self, s, step=4):
        lines = []
        for md in s.getElementsByClass('Metadata'):
            lines.append(f'title: {md.title}\n')
            lines.append(f'composer: {md.composer}\n')
            lines.append('tempo: 120\n')
            break
        for t in s.recurse().getElementsByClass(meter.TimeSignature):
            lines.append(f'ts: {t.ratioString}\n')
            self.ts = t.ratioString
            break
        s = s.voicesToParts()
        lines = lines + ['\n@instrument_start\n']
        for i in range(1, len(s.parts) + 1):
            lines.append('p{:02} = melody{:02}, Piano, 0, F\n'.format(i, i))
        lines = lines + ['@instrument_end\n']
        lines = lines + ['\n@group_start\n']
        lines = lines + ['@group_end\n']
        lines = lines + ['\n@macro_start\n']
        lines = lines + ['@macro_end\n']
        lines = lines + ['\n@start\n']
        # measure count
        offset = 1
        mcount = len(s.parts[0].measureOffsetMap())
        for i in range(mcount // step):
            offset, l = self.addmeasures(s, step, offset)
            lines = lines + l
        dmod = mcount % step
        if dmod > 0:
            _, l = self.addmeasures(s, dmod, offset)
        lines = lines + l
        lines = lines + ['@end\n']

        return lines


def getopts():
    parser = argparse.ArgumentParser(description='arguments ArgumentParser.')
    parser.add_argument('-i', '--input', type=str, required=True)
    parser.add_argument('-o', '--output', type=str, required=True)
    args = parser.parse_args()
    return args


if __name__ == '__main__':
    opts = getopts()
    cvt = CBConverter()
    s = converter.parse(opts.input)
    with open(opts.output, mode='w') as f:
        lines = cvt.process(s, step=4)
        f.writelines(lines)