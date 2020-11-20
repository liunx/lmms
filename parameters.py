
class Param:

    bar_length_table = {
        '4/4': 192,
        '3/4': 142,
        '2/4': 96,
        '5/4': 240,
        '6/4': 288,
        '3/8': 72,
        '6/8': 156,
        '7/8': 168,
        '9/8': 216,
        '12/8': 288
    }

    time_signature_map = {
        '4/4': 'r1',
        '3/4': 'r2.',
        '2/4': 'r2',
        '3/8': 'r4.',
        '6/8': 'r2.',
    }

    notation_length_map = {
        'whole': 1,
        'half': 2,
        'quarter': 4,
        'eighth': 8,
        '16th': 16,
        '32nd': 32,
    }

    whole_length = 192
    quarter_length = 48
