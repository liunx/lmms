import sys
import algorithm as alg
from parameters import Percussion
import models
import numpy as np

style = 'demo02'

def callback(rn):
    matrix = np.array(models.beats_patterns['dance'])
    emotion = rn['emotion']
    params = [0, 0, 0]
    if emotion == 'tender':
        params = [4, 6, 0]
    elif emotion == 'happy':
        params = [3, 4, 0]
    elif emotion == 'excited':
        params = [3, 5, 2]
    elif emotion == 'start':
        if rn['meter'] == '1/2':
            matrix = np.array(models.beats_start)
    elif emotion == 'stop':
        matrix = np.array(models.beats_stop)

    beats = alg.beats_algorithm01(matrix, *params)
    instruments = models.group01
    # final
    return beats, instruments