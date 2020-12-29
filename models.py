from parameters import Percussion

rock = [
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
    [1, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0]]

dance = [
    [0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0],
    [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
    [1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0]]

pattern01 = [
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
    [1, 0, 1, 0, 0, 0, 0, 1, 1, 0, 1, 0, 0, 0, 0, 0]]

triple01 = [
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0],
    [1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0]]

beats_patterns = {
    'rock': rock, 'dance': dance, 'pattern01': pattern01, 'triple01': triple01}

group01 = [
    Percussion.ClosedHiHat,
    Percussion.AcousticSnare,
    Percussion.AcousticBassDrum]

group02 = [
    Percussion.ClosedHiHat,
    Percussion.HandClap,
    Percussion.BassDrum1]

group03 = [
    Percussion.PedalHiHat,
    Percussion.AcousticSnare,
    Percussion.BassDrum1]

staff_beats = {
    'key': 'C',
    'tempo': '90',
    'timesign': '4/4',
    'tracks': {'beats': [
        'beat',
        'Percussion',
        '0',
        'F']},
    'playtracks': {
        'beats': {
            'noteset': [],
            'styles': [],
            'roman_numerals': [],
            'emotions': [],
            'instructions': [],
            'total_len': 0}}}

cbd_beats = {
    'info': {
        'key': 'C',
        'title': 'Beats Templates',
        'name': 'Beats Templates',
        'composer': 'CoderBand',
        'tempo': '90',
        'style': 'rock',
        'timesign': '4/4'},
    'tracks': {
        'beats': [
            'beat',
            'Percussion',
            '0',
            'F']},
    'clips': {},
    'playtracks': {
        'beats': ['c1']}}

staff_rhythm = {
    'key': 'C',
    'tempo': '90',
    'timesign': '4/4',
    'tracks': {'rhythm': [
        'rhythm',
        'EFBass',
        '0',
        'F']},
    'playtracks': {
        'rhythm': {
            'noteset': [],
            'styles': [],
            'roman_numerals': [],
            'emotions': [],
            'instructions': [],
            'total_len': 0}}}

cbd_rhythm = {
    'info': {
        'key': 'C',
        'title': 'Beats Templates',
        'name': 'Beats Templates',
        'composer': 'CoderBand',
        'tempo': '90',
        'style': 'rock',
        'timesign': '4/4'},
    'tracks': {
        'rhythm': [
            'rhythm',
            'EFBass',
            '0',
            'F']},
    'clips': {},
    'playtracks': {
        'rhythm': ['c1']}}
