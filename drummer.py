import time
import pygame
from fractions import Fraction


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


def demo01():
    song = [rock_prime[0], rock_vice[0]] * 2
    song += [rock_prime[1], rock_vice[1]] * 2
    song += [rock_prime[2], rock_vice[2]] * 2
    drum = Drummer()
    drum.load_sounds(instruments[0])
    drum.play_song(4, 110, song)


if __name__ == '__main__':
    demo01()
