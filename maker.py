import re
import music21 as m21
from analysis import Beats, Melody, Rhythm


class Maker:
    def __init__(self, data):
        self.init_data = data
        self.styles = []
        self.roman_numerals = []
        self.instructions = []
        self.emotions = []
        self.all_tracks = {}

    def make_beats(self):
        pass

    def make_rhythm(self):
        pass

    def make_melody(self):
        pass

    def process(self, cbd):
        self.info = cbd['info']
        self.tracks = cbd['tracks']
        self.playbacks = cbd['playbacks']
        for k, v in self.playbacks.items():
            ml = Melody(v)
            self.roman_numerals.extend(ml.roman_numerals)
            self.styles.extend(ml.styles)
            self.emotions.extend(ml.emotions)
            self.instructions.extend(ml.instructions)
            self.all_tracks[k] = ml.noteset

        print(self.playbacks)
        print(self.roman_numerals)

