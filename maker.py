import re
import music21 as m21
from analysis import Analysis


class Maker:
    time_signature_table = {
        '4/4': 48, '3/4': 36, '2/4': 24, '5/4': 60,
        '6/4': 72, '3/8': 18, '6/8': 36, '7/8': 42,
        '9/8': 54, '12/8': 72}

    def __init__(self, data):
        self.init_data = data
        self.styles = []
        self.roman_numerals = []
        self.instructions = []
        self.emotions = []
        self.all_tracks = {}
        self.timesigns = []

    def get_timesigns(self, data):
        pass

    def make_beats(self, data):
        pass

    def make_rhythm(self, data):
        # checking time signature
        ts = self.info['timesign']
        meter = self.time_signature_table[ts]
        offset = 0
        while offset < data['total_len']:
            offset += meter

    def compose(self, data, track_name):
        _attrib = self.tracks[track_name]
        track_attrib = dict(
            zip(['name', 'instrument', 'pitch', 'muted'], _attrib))
        data['track_attrib'] = track_attrib
        if track_attrib['instrument'] == 'Percussion':
            self.make_beats(data)
        else:
            self.make_rhythm(data)

    def process(self, cbd):
        self.info = cbd['info']
        self.tracks = cbd['tracks']
        self.playbacks = cbd['playbacks']
        for k, v in self.playbacks.items():
            al = Analysis(v)
            self.compose(al.get_result(), k)
