import time
import mido
from mido import Message, MetaMessage, MidiFile, MidiTrack


class Midi:
    # 88 keyboard
    key_range = 88
    key_start = 21
    key_stop = 108

    def __init__(self, staff, matrix):
        self._staff = staff
        self._matrix = matrix
        self.mid = MidiFile(ticks_per_beat=48)
        self.process()

    def add_header(self):
        staff = self._staff
        meta_track = MidiTrack()
        self.mid.tracks.append(meta_track)
        meta_track.append(MetaMessage(
            'copyright', text='(C) Coderband <liunx163@163.com> {}'.format(time.strftime("%Y"))))
        meta_track.append(MetaMessage('track_name', name=staff['title']))
        meta_track.append(MetaMessage(
            'text', text='Composer: {}'.format(staff['composer'])))
        meta_track.append(MetaMessage('key_signature', key=staff['key']))
        ts = staff['timesign'].split('/')
        meta_track.append(MetaMessage('time_signature',
                                      numerator=int(ts[0]), denominator=int(ts[1])))
        tempo = mido.bpm2tempo(int(staff['tempo']))
        meta_track.append(MetaMessage('set_tempo', tempo=tempo))
        meta_track.append(MetaMessage('end_of_track'))

    def add_track(self, ch, midis, track):
        keys = list(midis.keys())
        keys.sort()
        offset = 0
        for k in keys:
            _midis = midis[k]
            _midi = _midis[0]
            _time = k - offset
            # note on
            track.append(Message('note_on', channel=ch, note=_midi[0], velocity=64, time=_time))
            for _midi in _midis[1:]:
                track.append(Message('note_on', channel=ch, note=_midi[0], velocity=64, time=0))
            # note off
            track.append(Message('note_off', channel=ch, note=_midi[0], velocity=64, time=_midi[1]))
            offset = k + _midi[1]
            for _midi in _midis[1:]:
                track.append(Message('note_off', channel=ch, note=_midi[0], velocity=64, time=0))

    def add_tracks(self):
        channels = [i for i in range(16)]
        channels.remove(9)
        tracks = self._staff['playtracks']
        for k, v in tracks.items():
            # ignore empty tracks
            if 'matrix_index' not in v:
                continue
            ch = channels.pop(0)
            idx = v['matrix_index']
            matrix = self._matrix[idx]
            track = MidiTrack()
            self.mid.tracks.append(track)
            track.append(MetaMessage('track_name', name=k))
            track.append(MetaMessage(
                'instrument_name', name=v['instrument'][1]))
            midis = self.find_midis(matrix)
            self.add_track(ch, midis, track)

    def find_midis(self, matrix, offset_start=0, offset_len=0):
        midis = {}
        col, row = matrix.shape
        if offset_len <= 0 or offset_start + offset_len > col:
            offset_stop = col
        else:
            offset_stop = offset_start + offset_len
        for j in range(row):
            cnt = 0
            offset = -1
            for i in range(offset_start, offset_stop):
                if matrix[i][j] == 3:
                    cnt += 1
                    if offset < 0:
                        offset = i
                elif matrix[i][j] == 2:
                    cnt += 1
                    midi = j + self.key_start
                    if offset not in midis:
                        midis[offset] = [[midi, cnt]]
                    else:
                        midis[offset] += [[midi, cnt]]
                    cnt = 0
                    offset = -1
        return midis

    def process(self):
        self.add_header()
        self.add_tracks()

    def data(self):
        return self.mid

    def save(self, filename):
        self.mid.save(filename)
