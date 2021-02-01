import time
import pygame
import xmltodict
from fractions import Fraction
from parameters import Percussion
from collections import OrderedDict


instruments = [
    [
        '/usr/share/lmms/samples/drums/kick01.ogg',
        '/usr/share/lmms/samples/drums/snare01.ogg',
        '/usr/share/lmms/samples/drums/hihat_closed01.ogg',
        '/usr/share/lmms/samples/drums/hihat_opened01.ogg',
    ],
    [
        '/usr/share/hydrogen/data/drumkits/TR808EmulationKit/808_Kick_Long.flac',
        '/usr/share/hydrogen/data/drumkits/TR808EmulationKit/808_Snare_1.flac',
        '/usr/share/hydrogen/data/drumkits/TR808EmulationKit/808_Hat_Closed.flac',
        '/usr/share/hydrogen/data/drumkits/TR808EmulationKit/808_Hat_Open.flac',
    ],
    [
        '/usr/share/hydrogen/data/drumkits/GMkit/kick_Dry_b.flac',
        '/usr/share/hydrogen/data/drumkits/GMkit/sn_Jazz_c.flac',
        '/usr/share/hydrogen/data/drumkits/GMkit/hhc_Dry_a.flac',
        '/usr/share/hydrogen/data/drumkits/GMkit/hhc_Rock_b.flac',
    ],
    [
        '/usr/share/lmms/samples/drums/kick01.ogg',
        '/usr/share/lmms/samples/drums/snare01.ogg',
    ],
]

rock_prime = [
    [
        [1, 0, 0, 0, 1, 1, 0, 0],
        [0, 1, 0, 1],
        [1] * 8,
    ],
    [
        [1, 0, 0, 0, 1, 1, 0, 1],
        [0, 1, 0, 1],
        [1] * 7 + [0],
        [0] * 7 + [1],
    ],
    [
        [1, 0, 0, 1, 0, 1, 0, 0],
        [0, 1, 0, 1],
        [1] * 8,
    ],
    [
        [1, 0, 0, 0, 1, 1, 0, 0],
        [0, 1, 0, 1],
        [1, 1, 1, 1],
    ],
    [
        [1, 0, 0, 0, 1, 1, 0, 1],
        [0, 1, 0, 1],
        [1] * 4,
        [0] * 7 + [1],
    ],
    [
        [1, 0, 0, 1, 0, 1, 0, 0],
        [0, 1, 0, 1],
        [1, 1, 1, 1],
    ],
]

rock_vice = [
    [
        [1, 1, 0, 1, 0, 1, 0, 0],
        [0, 1, 0, 1],
        [1, 1, 1, 1, 1, 1, 1, 1],
    ],
    [
        [0, 1, 0, 0, 1, 1, 0, 1],
        [0, 1, 0, 1],
        [0, 1, 1, 1, 1, 1, 1, 1],
    ],
    [
        [1, 1, 0, 0, 1, 1, 0, 1],
        [0, 1, 0, 1],
        [1, 1, 1, 1, 1, 1, 1, 0],
        [0, 0, 0, 0, 0, 0, 0, 1]
    ],
    [
        [1, 1, 0, 1, 0, 1, 0, 0],
        [0, 1, 0, 1],
        [1, 1, 1, 1],
    ],
]


class Drummer:
    meter_len = 6

    def __init__(self):
        pygame.mixer.init()

    def __del__(self):
        pygame.mixer.quit()

    def load_sounds(self, instrums):
        self.sounds = []
        for i in instrums:
            if i:
                s1 = pygame.mixer.Sound(i)
                s2 = pygame.mixer.Sound(i)
                self.sounds.append([s1, s2])
            else:
                self.sounds.append(None)

    def play_sounds(self, pattern, delay):
        width = len(pattern[0])
        _min = min(len(pattern), len(self.sounds))
        for i in range(width):
            for i_ in range(_min):
                s = self.sounds[i_]
                if not s:
                    continue
                p = pattern[i_]
                if p[i] > 0:
                    if i % 2 > 0:
                        s[0].play()
                        s[1].stop()
                    else:
                        s[1].play()
                        s[0].stop()
            pygame.time.delay(delay)

    def play_pattern(self, ts, bpm, pattern, times=4):
        width = len(pattern[0])
        delay = int(60000 * ts / bpm / width)
        p = self.beat_box(pattern, ts)
        for _ in range(times):
            self.play_sounds(p, delay)

    def play_song(self, ts, bpm, patterns):
        delay = int(60000 / bpm / self.meter_len)
        for _pattern in patterns:
            p = self.beat_box(_pattern, ts)
            self.play_sounds(p, delay)

    def rotate(self, l, clockwise=False):
        if clockwise:
            l.insert(0, l[-1])
            l.pop()
        else:
            l.append(l[0])
            l.pop(0)

    def zoom_in(self, l, multiple=1):
        _l = [0] * int(len(l) * multiple)
        for i in range(len(l)):
            if l[i] > 0:
                _l[int(i * multiple)] = l[i]
        return _l

    def beat_box(self, beats, ts=4):
        _beats = []
        for l in beats:
            _len = len(l)
            bar_len = self.meter_len * ts
            m = Fraction(bar_len, _len)
            _beats.append(self.zoom_in(l, m))
        return _beats


class Hydrogen:
    pattern_size = 192
    template = 'data/default.h2song'
    pattern_dict = OrderedDict([('name', 'pattern 1-1'),
                                ('category', None),
                                ('size', '192'),
                                ('info', None),
                                ('noteList', None)])
    note_dict = OrderedDict([('position', '0'),
                             ('leadlag', '0'),
                             ('velocity', '0.8'),
                             ('pan_L', '0.5'),
                             ('pan_R', '0.5'),
                             ('pitch', '0'),
                             ('probability', '1'),
                             ('key', 'C0'),
                             ('length', '-1'),
                             ('instrument', '0'),
                             ('note_off', 'false')])

    def __init__(self):
        with open(self.template) as f:
            self.default = xmltodict.parse(f.read(), process_namespaces=True)
            self.default['song']['patternList']['pattern'] = []

    def load_instruments(self, xml):
        self.midi_map = {}
        with open(xml) as f:
            drumkit = xmltodict.parse(f.read())
        instruments = drumkit['drumkit_info']['instrumentList']['instrument']
        for i in instruments:
            i['drumkit'] = drumkit['drumkit_info']['name']
            self.midi_map[int(i['midiOutNote'])] = i
        self.default['song']['instrumentList'] = {'instrument': instruments}

    def save(self, xml):
        with open(xml, 'w') as f:
            f.write(xmltodict.unparse(self.default, pretty=True))

    def add_note(self, instrument, offset):
        ndict = self.note_dict.copy()
        ndict['position'] = offset
        ndict['instrument'] = instrument['id']
        return ndict

    def add_notes(self, instrument, pattern):
        notes = []
        plen = len(pattern)
        if self.pattern_size % plen > 0:
            raise ValueError('Pattern length is fault!')
        unit = self.pattern_size // plen
        for i in range(plen):
            if pattern[i] > 0:
                notes.append(self.add_note(instrument, i * unit))
        return notes

    def add_pattern(self, name, pattern):
        pdict = self.pattern_dict.copy()
        pdict['name'] = name
        notes = []
        for k, v in pattern.items():
            if k in self.midi_map:
                notes += self.add_notes(self.midi_map[k], v)
        pdict['noteList'] = {'note': notes}
        self.default['song']['patternList']['pattern'].append(pdict)


def demo01():
    song = [rock_prime[0], rock_vice[0]] * 2
    song += [rock_prime[1], rock_vice[1]] * 2
    song += [rock_prime[2], rock_vice[2]] * 2
    drum = Drummer()
    drum.load_sounds(instruments[0])
    drum.play_song(4, 110, song)


def demo02():
    rock_prime = [
        {
            Percussion.BassDrum1: [1, 0, 0, 0, 1, 1, 0, 0],
            Percussion.ElectricSnare: [0, 1, 0, 1],
            Percussion.ClosedHiHat: [1] * 8,
        },
    ]
    s = '/home/leiliu/Work/sources/hydrogen/data/drumkits/TR808EmulationKit/drumkit.xml'
    h2 = Hydrogen()
    h2.load_instruments(s)
    for p in rock_prime:
        h2.add_pattern('rock01', p)

    h2.save('xxx.h2song')


if __name__ == '__main__':
    demo02()
