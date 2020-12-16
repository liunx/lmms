import re
import copy
import music21 as m21
from analysis import Analysis
from common import Note
from creator import Rhythm, Melody, Beats


class Maker(Note):

    def __init__(self, data):
        self.init_data = data

    def update_global_info(self, staff):
        # TODO
        info = {}
        staff['global'] = info

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
        #melody.process()
        self.update_cbd_playtracks(staff, cbd)
