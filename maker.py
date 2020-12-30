import re
import copy
import sys
import music21 as m21
from analysis import Analysis
from common import Note
from creator import Rhythm, Melody, Beats


class Maker(Note):

    def __init__(self, data):
        self.init_data = data

    def divide_roman_numeral(self, pos, rn):
        _start = rn['offset']
        _stop = rn['offset'] + rn['len']
        _rn = rn.copy()
        _rn['len'] = pos - _start
        rn['offset'] = pos
        rn['len'] = _stop - pos
        return _rn, rn

    def segment_roman_numerals(self, staff):
        playtracks = staff['playtracks']
        for k, v in playtracks.items():
            rns = v['roman_numerals']
            if not rns:
                continue
            total_len = v['total_len']
            styles = v['styles']
            keys = v['keys']
            time_signs = v['time_signs']
            emotions = v['emotions']
            instructions = v['instructions']
            i = 0
            _rns = []
            time_sign = staff['timesign']
            key = staff['key']
            meter_len = self.bar_length_table[time_sign]
            style = None
            emotion = None
            instruction = None
            rn = None
            while i < total_len:
                if i in time_signs:
                    meter_len = self.bar_length_table[time_signs[i]]
                need_divide = False
                if i in emotions:
                    emotion = emotions[i]
                    if rn and emotion != rn['emotion']:
                        need_divide = True
                if i in styles:
                    style = styles[i]
                    if rn and style != rn['style']:
                        need_divide = True
                if i in keys:
                    key = keys[i]
                    if rn and key != rn['key']:
                        need_divide = True
                if i in instructions:
                    instruction = instructions[i]
                    if rn and instruction != rn['instruction']:
                        need_divide = True
                if need_divide:
                    _rn, rn = self.divide_roman_numeral(i, rn)
                    _rns.append(_rn)
                    rn['key'] = key
                    rn['style'] = style
                    rn['emotion'] = emotion
                    rn['instruction'] = instruction
                if i in rns:
                    rn = rns[i]
                    rn['emotion'] = emotion
                    rn['style'] = style
                    rn['key'] = key
                    rn['instruction'] = instruction
                    rn['timesign'] = time_sign
                    rn['meter_len'] = meter_len
                # divide meters
                if rn:
                    _start = rn['offset']
                    _stop = rn['offset'] + rn['len']
                    if i == _stop - 1:
                        _rns.append(rn)
                        rn = None
                        i += 1
                        continue
                    if i > 0 and i % meter_len == 0:
                        if i > _start and i < _stop:
                            _rn, rn = self.divide_roman_numeral(i, rn)
                            _rns.append(_rn)
                i += 1
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
            al = Analysis(staff, v)
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
