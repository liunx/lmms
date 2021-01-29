import sys
import algorithm as alg
from parameters import Param, Percussion
import models
import numpy as np

style = 'demo'

basic_pattern = [
    [0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0],
    [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
    [1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0]]

instruments = [
    Percussion.ClosedHiHat,
    Percussion.AcousticSnare,
    Percussion.AcousticBassDrum]

emotion_history = [None]
instruction_history = [None]


def get_melody(staff):
    melody = {}
    playtracks = staff['playtracks']
    tracks = staff['tracks']
    for k, v in playtracks.items():
        if tracks[k][4] == 'M':
            for note in v['noteset']:
                if note['offset'] in melody:
                    melody[note['offset']].append(note)
                else:
                    melody[note['offset']] = [note]
    return melody


def add_accent(staff, rn):
    notes = []
    ts = rn['timesign']
    _len = Param.bar_length_table[ts]
    melody = get_melody(staff)
    begin = rn['offset']
    end = begin + rn['len']
    for k, v in melody.items():
        if k >= begin and k < end:
            notes += v
    offsets = []
    for n in notes:
        offsets.append(int(n['offset']))
    l = np.array(offsets)
    l = l - l[0]
    gcd = np.gcd.reduce(l)
    if gcd > 0:
        l = l // gcd
        matrix_len = _len // gcd
    else:
        l = [0]
        matrix_len = 4
    matrix = np.array([[0] * matrix_len] * 3)
    for i in l:
        matrix[0][i] = 1
        matrix[1][i] = 1
        matrix[2][i] = 1
    return matrix


class Beats:
    def __init__(self):
        pass

    def enter(self, rn):
        raise NotImplementedError

    def quit(self, rn):
        raise NotImplementedError

    def accent(self, rn):
        raise NotImplementedError

    def fill(self, rn):
        raise NotImplementedError

    def default(self, rn):
        raise NotImplementedError

    def process(self, staff, track, rn):
        instruction = rn['instruction']
        if instruction == 'enter':
            return self.enter(rn)
        elif instruction == 'accent':
            return self.accent(rn)
        elif instruction == 'fill':
            return self.fill(rn)
        elif instruction == 'quit':
            return self.quit(rn)
        else:
            return self.default(rn)


class MyBeats(Beats):
    blank_matrix = [[0] * 16] * 3
    instruments = [
        Percussion.ClosedHiHat,
        Percussion.AcousticSnare,
        Percussion.AcousticBassDrum]

    def emotion(self, emotion, matrix):
        m = []
        if emotion in ['scared', 'sad', 'tender']:
            m = alg.beats_algorithm01(matrix, b=4, m=4, h=0)
        elif emotion in ['happy', 'excited', 'angry']:
            m = alg.beats_algorithm01(matrix, b=2, m=2, h=0)
        else:
            raise ValueError('Unknown emotion: {}!'.format(emotion))
        return m

    def enter(self, rn):
        print(rn)
        emotion = rn['emotion']
        m = np.array(self.blank_matrix.copy())
        instruments = self.instruments.copy()
        if rn['meter'] == '1/2':
            m = np.array_split(m, 2, axis=1)[0]
        elif rn['meter'] == '1':
            pass
        else:
            raise ValueError('Unsupported meter: {}!'.format(rn['meter']))
        m = self.emotion(emotion, m)
        return m, instruments

    def quit(self, rn):
        emotion = rn['emotion']
        if rn['meter'] == '1/2':
            matrix = np.array(models.beats_stop)
        elif rn['meter'] == '1':
            pass
        else:
            raise ValueError

    def accent(self, rn):
        pass

    def fill(self, rn):
        pass

    def default(self, rn):
        pass


my_beats = MyBeats()


def callback(staff, track, rn):
    global my_beats
    my_beats.process(staff, track, rn)

    _instruments = instruments.copy()
    matrix = np.array(basic_pattern)
    emotion = rn['emotion']
    instruction = rn['instruction']
    if instruction == 'enter':
        if rn['meter'] == '1/2':
            matrix = np.array(models.beats_start)
    elif instruction == 'accent':
        matrix = add_accent(staff, rn)
        _instruments[0] = Percussion.CrashCymbal1
        _instruments[1] = Percussion.AcousticSnare
        emotion = None
    elif instruction == 'quit':
        matrix = np.array(models.beats_stop)
    # emotion
    params = [0, 0, 0]
    if emotion == 'sad':
        params = [0, 0, -2]
        _instruments[1] = Percussion.SideStick
    elif emotion == 'scared':
        params = [0, -1, -1]
    elif emotion == 'tender':
        params = [0, 0, 0]
        #_instruments[1] = Percussion.SideStick
    elif emotion == 'happy':
        params = [0, 4, 0]
    elif emotion == 'excited':
        params = [0, 0, 2]
        _instruments[0] = Percussion.OpenTriangle
    elif emotion == 'angry':
        params = [3, 6, 2]
        _instruments[2] = Percussion.BassDrum1

    beats = alg.beats_algorithm01(matrix, *params)
    # final
    return beats, _instruments
