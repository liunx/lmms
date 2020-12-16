
NOTE_LEN_1ST = 192
NOTE_LEN_2ND = 96
NOTE_LEN_4TH = 48
NOTE_LEN_8TH = 24
NOTE_LEN_16TH = 12
NOTE_LEN_32ND = 6
NOTE_LEN_64TH = 3


class NoteLen:
    _1st = 192
    _2nd = 96
    _4th = 48
    _8th = 24
    _16th = 12
    _32nd = 6
    _64th = 3


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

    matrix_length_table = {
        '4/4': 16,
        '3/4': 12,
        '2/4': 8,
        '5/4': 20,
        '6/4': 24,
        '3/8': 6,
        '6/8': 12,
        '7/8': 14,
        '9/8': 18,
        '12/8': 24
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


class Percussion:
    AcousticBassDrum = 35
    BassDrum1 = 36
    SideStick = 37
    AcousticSnare = 38
    HandClap = 39
    ElectricSnare = 40
    LowFloorTom = 41
    ClosedHiHat = 42
    HighFloorTom = 43
    PedalHiHat = 44
    LowTom = 45
    OpenHiHat = 46
    LowMidTom = 47
    HiMidTom = 48
    CrashCymbal1 = 49
    HighTom = 50
    RideCymbal1 = 51
    ChineseCymbal = 52
    RideBell = 53
    Tambourine = 54
    SplashCymbal = 55
    Cowbell = 56
    CrashCymbal2 = 57
    Vibraslap = 58
    RideCymbal2 = 59
    HiBongo = 60
    LowBongo = 61
    MuteHiConga = 62
    OpenHiConga = 63
    LowConga = 64
    HighTimbale = 65
    LowTimbale = 66
    HighAgogo = 67
    LowAgogo = 68
    Cabasa = 69
    Maracas = 70
    ShortWhistle = 71
    LongWhistle = 72
    ShortGuiro = 73
    LongGuiro = 74
    Claves = 75
    HiWoodBlock = 76
    LowWoodBlock = 77
    MuteCuica = 78
    OpenCuica = 79
    MuteTriangle = 80
    OpenTriangle = 81
