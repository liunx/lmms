import numpy as np
from parameters import NoteLen
import parameters as param
import algorithm as alg

style = 'demo'

scales = 25


def generate_matrix(matrix, vectors):
    w = len(matrix[0])
    m = [[0] * w] * scales
    i = 0
    for v in vectors:
        m[v] = matrix[i]
        i += 1
    return np.array(m)


def keyboard(staff, rn):
    table = np.array([1, 1, 1, 1, 1, 1, 1, 1])
    if rn['len'] < NoteLen._1st:
        table = np.split(table, NoteLen._1st // rn['len'])[0]
    vectors = [0, 4, 7, 12]
    _key = param.modes[rn['key'].upper()]
    _rn = param.roman_numerals[rn['roman_numeral'].upper()]
    base_midi = _key + _rn
    m = alg.wave_sawi(table, len(vectors))
    matrix = generate_matrix(m, vectors)
    return base_midi, matrix


def bass(staff, rn):
    table = np.array([3, 1, 2, -1, 1])
    #table = np.array([1, 1, 1, 1, 1, 1, -1, 1])
    if rn['meter'] == '1/2':
        table = np.array([3, -1])
    vectors = [0]
    _key = param.modes[rn['key'].upper()]
    _rn = param.roman_numerals[rn['roman_numeral'].upper()]
    base_midi = _key + _rn - 12
    m = alg.wave_sawi(table, len(vectors))
    matrix = generate_matrix(m, vectors)
    return base_midi, matrix


def callback(staff, track, rn):
    if track[1].endswith('Piano'):
        return keyboard(staff, rn)
    elif track[1].endswith('Bass'):
        return bass(staff, rn)
