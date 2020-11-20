import re
import copy
import music21 as m21
from analysis import Analysis
from common import Note


class Maker(Note):
    time_signature_table = {
        '4/4': 192, '3/4': 142, '2/4': 96, '5/4': 240,
        '6/4': 288, '3/8': 72, '6/8': 156, '7/8': 168,
        '9/8': 216, '12/8': 288}

    def __init__(self, data):
        self.init_data = data
        self.styles = []
        self.roman_numerals = []
        self.instructions = []
        self.emotions = []
        self.all_tracks = {}
        # TODO
        self.global_timesigns = []
        # TODO
        self.global_pitches = []

    def get_timesigns(self, data):
        pass

    def make_beats(self, data):
        pass

    def get_dimension(self, testlist, dim=0):
        if isinstance(testlist, list):
            if testlist == []:
                return dim
            dim = dim + 1
            dim = self.get_dimension(testlist[0], dim)
            return dim
        else:
            if dim == 0:
                return -1
            else:
                return dim

    def find_offsets(self, data, offset, meter):
        l = []
        for d in data:
            _offset = d['offset']
            if _offset >= offset and _offset < (offset + meter):
                l.append(d)
        return l

    def cut_set(self, rn, offset, meter):
        head = None
        tail = None
        head_len = offset + meter - rn['offset']
        if rn['len'] > head_len:
            tail_len = rn['len'] - head_len
            tail = dict(rn)
            tail['offset'] = offset + meter
            tail['len'] = tail_len
            head = dict(rn)
            head['len'] = head_len
        return (head, tail)

    def fill_rhythm(self, data, rn, timesign, meter, noteset, offset):
        rf = m21.roman.RomanNumeral(
            rn['roman_numeral'], self.current_info['key'])
        # find the basic unit of beat per meter
        d = {'midi': rf.root().midi, 'len': rn['len'], 'offset': offset}
        noteset.append(d)

    def expand_roman_numerals(self, data, offset, timesign, meter, noteset):
        roman_numerals = data['roman_numerals']
        if not roman_numerals:
            return None
        rns = self.find_offsets(roman_numerals, offset, meter)
        if not rns:
            return None
        for rn in rns:
            if rn['offset'] + rn['len'] > offset + meter:
                # cut down in meter size
                head, tail = self.cut_set(rn, offset, meter)
                if tail:
                    roman_numerals.insert(0, tail)
                self.fill_rhythm(data, head, timesign, meter, noteset, offset)
            else:
                self.fill_rhythm(data, rn, timesign, meter, noteset, offset)
            roman_numerals.remove(rn)

    def make_rhythm(self, data):
        # checking time signature
        ts = self.info['timesign']
        meter = self.time_signature_table[ts]
        noteset = []
        offset = 0
        self.current_info = {}
        self.current_info['key'] = 'C'
        while offset < data['total_len']:
            # update time signature
            if self.get_timesigns:
                sets = self.find_offsets(self.global_timesigns, offset, meter)
                if sets:
                    _set = sets[0]
                    ts = _set['timesign']
                    self.current_info['timesign'] = ts
                    meter = self.time_signature_table[ts]
                    self.current_info['meter'] = meter
            # update tracks
            self.expand_roman_numerals(data, offset, ts, meter, noteset)
            offset += meter
        return noteset

    def compose(self, data, track_name):
        _attrib = self.tracks[track_name]
        track_attrib = dict(
            zip(['name', 'instrument', 'pitch', 'muted'], _attrib))
        data['track_attrib'] = track_attrib
        noteset = []
        if track_attrib['instrument'] == 'Percussion':
            noteset = self.make_beats(data)
        else:
            noteset = self.make_rhythm(data)
        d = []
        if data['noteset']:
            if self.get_dimension(data['noteset']) > 1:
                d.extend(data['noteset'])
            else:
                d.append(data['noteset'])
        if noteset:
            if self.get_dimension(noteset) > 1:
                d.extend(noteset)
            else:
                d.append(noteset)
        if d:
            self.all_tracks[track_name] = d

    def reform_noteset(self, noteset):
        d = {}
        key = 'offset'
        l = [i[key] for i in noteset]
        values = set(l)
        for v in values:
            ll = []
            for n in noteset:
                if n[key] == v:
                    ll.append(n)
            d[v] = ll
        return d

    def to_tinynotes(self, noteset):
        l = []
        _noteset = self.reform_noteset(noteset)
        current_len = 0
        offsets = list(_noteset.keys())
        offsets.sort()
        for offset in offsets:
            notes = _noteset[offset]
            if offset > current_len:
                rest_len = offset - current_len
                rests = self.fill_rests(rest_len)
                l += rests
            if len(notes) > 1:
                ll = ['chord']
                for n in notes:
                    ll += self.to_tinynote(n)
                l.append(ll)
                current_len = offset + n['len']
            else:
                l += self.to_tinynote(notes[0])
                current_len = offset + notes[0]['len']
        return l

    def update_playbacks(self):
        tracks = self.tracks.copy()
        self.tracks.clear()
        self.playbacks.clear()
        for k, v in self.all_tracks.items():
            for i in range(len(v)):
                track = tracks[k].copy()
                key = f'{k}{i+1}'
                track[0] = key
                self.tracks[key] = track
                play_track = self.to_tinynotes(v[i])
                self.playbacks[key] = play_track

    def process(self, cbd):
        self.info = cbd['info']
        self.tracks = cbd['tracks']
        self.playbacks = cbd['playbacks']
        for k, v in self.playbacks.items():
            al = Analysis(v)
            self.compose(al.get_result(), k)
        self.update_playbacks()
