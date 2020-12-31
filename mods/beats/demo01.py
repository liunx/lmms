import sys
import algorithm as alg
from parameters import Percussion
import models
import numpy as np

style = 'demo01'

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


def fill_array(l, x, _len):
    flag = False
    if x < 0:
        flag = True
    x = abs(x)
    if x > 0 and x < _len:
        for i in range(0, _len, x):
            if flag:
                l[i] = 0
            else:
                l[i] = 1


def algorithm01(matrix, b=0, m=0, h=0):
    _m = matrix.copy()
    _len = len(_m[0])
    fill_array(_m[0], h, _len)
    fill_array(_m[1], m, _len)
    fill_array(_m[2], b, _len)
    return _m


def callback(rn):
    _instruments = instruments.copy()
    matrix = np.array(basic_pattern)
    emotion = rn['emotion']
    instruction = rn['instruction']
    if instruction == 'begin':
        if rn['meter'] == '1/2':
            matrix = np.array(models.beats_start)
    elif instruction == 'end':
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
    elif emotion == 'happy':
        params = [0, 4, 0]
        _instruments[0] = Percussion.Cowbell
    elif emotion == 'excited':
        params = [0, 0, 2]
        _instruments[0] = Percussion.OpenTriangle
    elif emotion == 'angry':
        params = [3, 6, 2]
        _instruments[2] = Percussion.BassDrum1

    beats = algorithm01(matrix, *params)
    # final
    return beats, _instruments
