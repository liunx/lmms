import matrix
from parameters import Percussion

rock_prime = [
    [
        [1, 0, 0, 0, 1, 1, 0, 0],
        [0, 1, 0, 1],
        [1] * 8,
    ],
    [
        [1, 0, 0, 0, 1, 1, 0, 1],
        [0, 1, 0, 1],
        [1] * 7 + [0],
        [0] * 7 + [1],
    ],
    [
        [1, 0, 0, 1, 0, 1, 0, 0],
        [0, 1, 0, 1],
        [1] * 8,
    ],
    [
        [1, 0, 0, 0, 1, 1, 0, 0],
        [0, 1, 0, 1],
        [1, 1, 1, 1],
    ],
    [
        [1, 0, 0, 0, 1, 1, 0, 1],
        [0, 1, 0, 1],
        [1] * 4,
        [0] * 7 + [1],
    ],
    [
        [1, 0, 0, 1, 0, 1, 0, 0],
        [0, 1, 0, 1],
        [1, 1, 1, 1],
    ],
]

rock_vice = [
    [
        [1, 1, 0, 1, 0, 1, 0, 0],
        [0, 1, 0, 1],
        [1, 1, 1, 1, 1, 1, 1, 1],
    ],
    [
        [0, 1, 0, 0, 1, 1, 0, 1],
        [0, 1, 0, 1],
        [0, 1, 1, 1, 1, 1, 1, 1],
    ],
    [
        [1, 1, 0, 0, 1, 1, 0, 1],
        [0, 1, 0, 1],
        [1, 1, 1, 1, 1, 1, 1, 0],
        [0, 0, 0, 0, 0, 0, 0, 1]
    ],
    [
        [1, 1, 0, 1, 0, 1, 0, 0],
        [0, 1, 0, 1],
        [1, 1, 1, 1],
    ],
]


class callbacks:
    @staticmethod
    def handle_key(offset, data, obj):
        pass

    @staticmethod
    def handle_emotion(offset, data, obj):
        pass

    @staticmethod
    def handle_instruction(offset, data, obj):
        pass

    @staticmethod
    def handle_rn(offset, data, obj):
        pass
