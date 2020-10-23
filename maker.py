import re


midi_map = {
    "r": 0, "R": 0,
    "CCCC": 12, "DDDD": 14, "EEEE": 16, "FFFF": 17, "GGGG": 19, "AAAA": 21, "BBBB": 23,
    "CCC": 24, "DDD": 26, "EEE": 28, "FFF": 29, "GGG": 31, "AAA": 33, "BBB": 35,
    "CC": 36, "DD": 38, "EE": 40, "FF": 41, "GG": 43, "AA": 45, "BB": 47,
    "C": 48, "D": 50, "E": 52, "F": 53, "G": 55, "A": 57, "B": 59,
    "c": 60, "d": 62, "e": 64, "f": 65, "g": 67, "a": 69, "b": 71,
    "c'": 72, "d'": 74, "e'": 76, "f'": 77, "g'": 79, "a'": 81, "b'": 83,
    "c''": 84, "d''": 86, "e''": 88, "f''": 89, "g''": 91, "a''": 93, "b''": 95,
    "c'''": 96, "d'''": 98, "e'''": 100, "f'''": 101, "g'''": 103, "a'''": 105, "b'''": 107,
}


class Maker:
    keywords = ['chord', 'triple']
    roman_numeral = None
    walking_bass = 'down'

    def __init__(self, data):
        self.init_data = data

    def calclen(self, s):
        num = 0
        dot = 0
        # Rest & Notation
        m = re.match(r'([a-grA-GR\'#-]+)(\d+)([.]*)', s)
        if m:
            num = int(m.group(2))
            dot = m.group(3).count('.')
        n1 = 32 / num
        curr = n1
        for _ in range(dot):
            n1 += curr / 2
            curr = curr / 2
        return n1

    def fill_rest(self, measure):
        if measure <= 0:
            return []
        rests = []
        m = measure
        for i, j in zip([32, 16, 8, 4, 2, 1], [1, 2, 4, 8, 16, 32]):
            q = int(m // i)
            r = int(m % i)
            if q > 0:
                rests += [f'r{j}'] * q
            if r == 0:
                break
            m = r
        rests.reverse()
        return rests

    def tracklen(self, track):
        tlen = 0
        for n in track:
            if type(n) == list:
                n = n[-1]
            tlen += self.calclen(n)
        return tlen

    def flatten_notes(self, notes):
        _notes = []
        for n in notes:
            if type(n) == list:
                if n[0] not in self.keywords:
                    _notes += n
            else:
                _notes.append(n)
        return _notes

    def update_notation(self, key_orig, notes):
        _notes = []
        key_curr = self.info['key']

        for n in notes:
            pass

    def expand_pattern(self, ref, offset, track_name, idx):
        info = self.init_data.get(ref)
        if not info:
            print("[Err] No found pattern {} !".format(ref))
            return 0
        track = self.tracks[track_name]
        # add new track
        max_pattern_len = 0
        for k, v in info['playbacks'].items():
            _offset = offset
            if self.roman_numeral:
                self.update_notation(info['info']['key'], v)
            _track_name = info['info']['id'] + k
            if _track_name not in self.tracks:
                self.tracks[_track_name] = track
                self.playbacks[_track_name] = self.fill_rest(_offset)
            ptrack = self.playbacks[_track_name]
            curr_len = self.tracklen(ptrack)
            pattern_len = self.tracklen(v)
            if max_pattern_len < pattern_len:
                max_pattern_len = pattern_len
            diff_len = _offset - curr_len
            if diff_len > 0:
                rests = self.fill_rest(diff_len)
                ptrack += rests
            ptrack += v
            _offset += pattern_len
        # fill the refer to rests
        notes = self.playbacks[track_name]
        notes[idx] = self.fill_rest(max_pattern_len)
        self.playbacks[track_name] = self.flatten_notes(notes)

        return _offset

    def update_playback(self):
        playbacks = dict(self.playbacks)
        for k, v in playbacks.items():
            offset = 0
            for i in range(len(v)):
                n = v[i]
                if type(n) == list:
                    n = n[-1]
                if n.startswith('$'):
                    offset = self.expand_pattern(
                        n.replace('$', ''), offset, k, i)
                elif n.startswith('!'):
                    self.roman_numeral = n.replace('!', '')
                    # rm roman numeral
                    self.playbacks[k][i] = ''
                elif n.startswith('~'):
                    self.walking_bass = n.replace('~', '')
                    self.playbacks[k][i] = ''
                else:
                    offset += self.calclen(n)

    def process(self, cbd):
        self.info = cbd['info']
        self.tracks = cbd['tracks']
        self.playbacks = cbd['playbacks']
        self.update_playback()
        print(self.info)
        print(self.playbacks)
