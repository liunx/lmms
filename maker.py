import re
import copy
import music21 as m21
from analysis import Analysis
from common import Note
from creator import Rhythm, Melody, Beats


class Maker(Note):

    def __init__(self, data):
        self.init_data = data

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

    def update_global_info(self, staff):
        # TODO
        info = {}
        staff['global'] = info

    def update_cbd_playtracks(self, staff, cbd):
        tracks = cbd['tracks']
        playtracks = cbd['playtracks']
        _tracks = tracks.copy()
        tracks.clear()
        playtracks.clear()
        for k, v in staff['playtracks'].items():
            noteset = v['noteset']
            if not noteset:
                continue
            dim = self.get_dimension(noteset)
            if dim <= 1:
                noteset = [noteset]
            for i in range(len(noteset)):
                track = _tracks[k].copy()
                key = f'{k}{i+1}'
                track[0] = key
                tracks[key] = track
                play_track = self.to_tinynotes(noteset[i])
                playtracks[key] = play_track

    def divide_roman_numeral(self, rn):
        rns = []
        start = int(rn['offset'])
        stop = int(rn['offset'] + rn['len'])
        meter = rn['meter_len']
        offsets = [start]
        for i in range(start + 1, stop):
            if i % meter == 0:
                offsets.append(i)
        offsets.append(stop)
        if len(offsets) == 2:
            return [rn]
        for i in range(len(offsets) - 1):
            offset1 = offsets[i]
            offset2 = offsets[i+1]
            _rn = rn.copy()
            _rn['offset'] = offset1
            _rn['len'] = offset2 - offset1
            rns.append(_rn)
            i += 1
        return rns

    def segment_roman_numerals(self, staff):
        playtracks = staff['playtracks']
        for k, v in playtracks.items():
            rns = v['roman_numerals']
            if not rns:
                continue
            ts = staff['timesign']
            _rns = []
            meter_len = self.bar_length_table[ts]
            for rn in rns:
                rn['timesign'] = ts
                rn['meter_len'] = meter_len
                _rns += self.divide_roman_numeral(rn)
            v['roman_numerals'] = _rns

    def process(self, cbd):
        staff = {}
        staff['key'] = cbd['info']['key']
        staff['title'] = cbd['info']['title']
        staff['composer'] = cbd['info']['composer']
        staff['tempo'] = cbd['info']['tempo']
        staff['timesign'] = cbd['info']['timesign']
        staff['tracks'] = cbd['tracks']
        playtracks = {}
        for k, v in cbd['playtracks'].items():
            al = Analysis(v)
            playtracks[k] = al.get_result()
        staff['playtracks'] = playtracks
        self.segment_roman_numerals(staff)
        # do pipelines
        beats = Beats(staff)
        rhythm = Rhythm(staff)
        melody = Melody(staff)
        beats.process()
        rhythm.process()
        melody.process()
        self.update_cbd_playtracks(staff, cbd)
