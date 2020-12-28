import sys
import inspect
import numpy as np
from parameters import NoteLen


def sine(matrix, step=1, size=1):
    _m = cos(matrix, step, size)
    return np.flipud(_m)


def cos(matrix, step=1, size=1):
    w = len(matrix[0])
    h = len(matrix) - 1
    offset = 0
    _divide = w // size
    for _ in range(size):
        idx = 0
        _step = 1
        for i in range(0, _divide, step):
            if idx > h:
                idx -= 2
                _step = -1
            elif idx < 0:
                idx += 2
                _step = 1
            matrix[idx][i + offset] = 3
            idx += _step
        offset += _divide
    return np.array(matrix)


def zoom_in(matrix, multiple=1):
    w = len(matrix[0])
    h = len(matrix)
    new_matrix = np.array([[0] * w * multiple] * h)
    for i in range(h):
        for j in range(w):
            if matrix[i][j] > 0:
                for _i in range(multiple):
                    new_matrix[i][j * multiple + _i] = 3
    return new_matrix


def get_len(matrix):
    count = 0
    for i in matrix:
        if i == 0:
            break
        elif i == 0b10:
            count += 1
            break
        count += 1
    return count


def to_table(matrix):
    table = []
    i = 0
    while i < len(matrix):
        if matrix[i] == 0:
            count = 0
            while i < len(matrix):
                if (matrix[i] != 0):
                    i -= 1
                    table.append(-count)
                    count = 0
                    break
                count += 1
                i += 1
            if count > 0:
                table.append(-count)
        elif matrix[i] == 0b10:
            table.append(1)
        elif matrix[i] == 0b11:
            count = 0
            while i < len(matrix):
                if matrix[i] == 0:
                    i -= 1
                    table.append(count)
                    count = 0
                    break
                if matrix[i] == 0b10:
                    table.append(count + 1)
                    count = 0
                    break
                i += 1
                count += 1
            if count > 0:
                table.append(count)
        i += 1
    return np.array(table)


def to_matrix(table):
    width = abs(table).sum()
    _matrix = np.array([0] * width)
    offset = 0
    for i in table:
        if i > 0:
            _matrix[offset: offset + i] = [3] * i
            _matrix[offset + i - 1] = 2
        else:
            i = abs(i)
            _matrix[offset: offset + i] = [0] * i
        offset += abs(i)
    return _matrix


def merge(table, step, shift=0):
    matrix = to_matrix(table)
    width = len(matrix)
    for i in range(shift, width, step):
        if matrix[i] == 0b10:
            matrix[i] = 0b11
    return to_table(matrix)


def fragment(table, step, divisor=1, shift=0):
    matrix = to_matrix(table)
    width = len(matrix)
    for i in range(shift, width, step):
        _len = get_len(matrix[i:])
        if divisor > 1:
            d = _len // divisor
            for j in range(1, divisor):
                matrix[i + d * j - 1] = 0b10
    return to_table(matrix)


def wave_cos(table, height):
    width = abs(table).sum()
    matrix = np.array([[0] * width] * height)
    idx = 0
    offset = 0
    direct = 1
    for _table in table:
        if _table > 0:
            if idx > height - 1:
                idx -= 2
                direct = - direct
            elif idx < 0:
                idx += 2
                direct = - direct
            matrix[idx][offset: offset + _table] = [3] * _table
            matrix[idx][offset + _table - 1] = 2
            idx += direct
        offset += abs(_table)
    return matrix


def wave_sine(table, height):
    return np.flipud(wave_cos(table, height))


def wave_sawi(table, height):
    return np.flipud(wave_saw(table, height))


def wave_saw(table, height):
    width = abs(table).sum()
    matrix = np.array([[0] * width] * height)
    idx = 0
    offset = 0
    for _table in table:
        if _table > 0:
            matrix[idx % height][offset: offset + _table] = [3] * _table
            matrix[idx % height][offset + _table - 1] = 2
            idx += 1
        offset += abs(_table)
    return matrix


divisors = [1, 2, 3, 4, 6, 8, 12, 16, 24, 32, 48, 64, 96, 192]


def table_demo01(table):
    print('==== {} ===='.format(inspect.stack()[0][3]))
    print(table)
    steps = [1, 2, 3, 4, 5, 6, 7, 8]
    shifts = [0, 2, 4, 6, 8]
    divisor = 2
    l = []
    for step in steps:
        for shift in shifts:
            print('divisor={},step={},shift={}:'.format(divisor, step, shift))
            _table = fragment(table, step, divisor, shift)
            t = _table.tolist()
            if t not in l:
                l.append(t)
            print(_table)
    return l


def table_demo02(table):
    print('==== {} ===='.format(inspect.stack()[0][3]))
    print(table)
    steps = [1, 2, 3, 4, 5, 6, 7, 8]
    shifts = [0, 2, 4, 6, 8]
    divisor = 2
    l = []
    for step in steps:
        for shift in shifts:
            print('divisor={},step={},shift={}:'.format(divisor, step, shift))
            _table = fragment(table, step, divisor, shift)
            t = _table.tolist()
            if t not in l:
                l.append(t)
            print(_table)
    return l


def matrix_demo01():
    print('==== {} ===='.format(inspect.stack()[0][3]))
    table = np.array([2, 2, 2, 2, 2, 2, 2, 2])
    print(table)
    m1 = wave_saw(table, 4)
    m2 = wave_sine(table, 4)
    m = m1 | m2
    print(m)


if __name__ == '__main__':
    table = np.array([4, 4, 4, 4])
    l = table_demo02(table)
    print(len(l))
