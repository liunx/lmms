import time
import threading
import fluidsynth
import mido
import jack
from mido import MidiFile
from fractions import Fraction
from threading import Event
from bisect import bisect_left


class Synth:
    sf2 = "/usr/share/sounds/sf2/FluidR3_GM.sf2"

    def __init__(self, name, samplerate, gain=1.0, sf2=None):
        fs = fluidsynth.Synth(gain, samplerate)
        fs.setting('midi.driver', 'jack')
        fs.setting('audio.jack.id', name)
        fs.setting('audio.jack.autoconnect', False)
        fs.start(driver='jack')
        if not sf2:
            fs.sfload(self.sf2)
        else:
            fs.sfload(sf2)
        fs.program_change(0, 0)
        self.fs = fs

    def close(self):
        self.fs.delete()


class Sequencer:
    def __init__(self, name):
        self.builtin_bpm = 120
        self.bpm = 120
        self.cursor_pos = 0
        self.last_pos = 0
        self.bpm_rate = Fraction(1, 1)
        self.msgs = {}
        self.msgs_keys = []
        self.cli = jack.Client(name)
        self.time_per_frame = Fraction(1, self.cli.samplerate)
        self.midi_port = self.cli.midi_outports.register(f'midi_out')
        self.cli.set_process_callback(self.process)
        self.cli.set_samplerate_callback(self.samplerate)
        self.cli.activate()

    def close(self):
        self.cli.close()

    def connect(self, port):
        self.midi_port.connect(port)

    def load_midi(self, mid):
        msgs = {}
        offset = 0
        _msgs = mido.merge_tracks(mid.tracks)
        self.mid = mid
        i = 0
        while i < len(_msgs):
            msg = _msgs[i]
            if msg.time > 0:
                offset += self.time_to_frames(msg.time)
            if offset in msgs:
                msgs[offset] += [msg]
            else:
                msgs[offset] = [msg]
            i += 1
        self.msgs = msgs
        self.msgs_keys = list(msgs.keys())
        self.msgs_keys.sort()

    def seek_msgs(self, pos_begin, pos_end):
        begin = bisect_left(self.msgs_keys, pos_begin)
        end = bisect_left(self.msgs_keys, pos_end)
        if begin >= end:
            return []
        return self.msgs_keys[begin:end]

    def time_to_frames(self, time_):
        time_per_beat = Fraction(60, self.builtin_bpm)
        frames_per_beat = time_per_beat / self.time_per_frame
        rate = Fraction(time_, self.mid.ticks_per_beat)
        frames = frames_per_beat * rate * self.bpm_rate
        return round(frames)

    def get_cursor_pos(self, start_pos, frames):
        pos = self.cursor_pos
        if self.last_pos == start_pos:
            pos = start_pos
        elif abs(self.last_pos + frames - start_pos) > 23:
            print('rewind! {}'.format(start_pos - self.last_pos))
            pos = start_pos
        self.last_pos = start_pos
        return pos

    def process(self, frames):
        stat = self.cli.transport_state
        if stat == jack.STOPPED:
            return
        if not bool(self.msgs_keys):
            return
        start_pos = self.cli.transport_frame
        # tempo may changed during playing
        # https://jackaudio.org/api/structjack__position__t.html
        pos = self.cli.transport_query_struct()[1]
        bpm = int(pos.beats_per_minute)
        if bpm > 0 and self.bpm != bpm:
            self.bpm = bpm
            self.bpm_rate = Fraction(bpm, self.builtin_bpm)
        cursor_pos = self.get_cursor_pos(start_pos, frames)
        _frames = int(frames * self.bpm_rate)
        self.cursor_pos = cursor_pos + _frames
        # follow transport_frame
        self.midi_port.clear_buffer()
        if stat in [jack.STARTING, jack.ROLLING]:
            offsets = self.seek_msgs(cursor_pos, cursor_pos + _frames)
            for offset in offsets:
                msgs = self.msgs[offset]
                _offset = int((offset - cursor_pos) / self.bpm_rate)
                for msg in msgs:
                    self.midi_port.write_midi_event(_offset, msg.bytes())

    def samplerate(self, samplerate):
        self.time_per_frame = Fraction(1, samplerate)


class TimebaseMaster(jack.Client):
    def __init__(self, name='TimebaseMaster', *, bpm=120.0, beats_per_bar=4, beat_type=4,
                 ticks_per_beat=1920, conditional=False, debug=False, **kw):
        super().__init__(name, **kw)
        self.beats_per_bar = beats_per_bar
        self.beat_type = beat_type
        self.bpm = bpm
        self.conditional = conditional
        self.ticks_per_beat = ticks_per_beat
        self.stop_event = Event()
        self.set_shutdown_callback(self.shutdown_callback)

    def shutdown_callback(self, status, reason):
        print('JACK shutdown:', reason, status)
        self.stop_event.set()

    def timebase_callback(self, state, nframes, pos, new_pos):
        if new_pos or self.need_update:
            self.need_update = False
            pos.beats_per_bar = self.beats_per_bar
            pos.beats_per_minute = self.bpm
            pos.beat_type = self.beat_type
            pos.ticks_per_beat = self.ticks_per_beat
            pos.valid = jack.POSITION_BBT

            minutes = pos.frame / (pos.frame_rate * 60.0)
            abs_tick = minutes * self.bpm * self.ticks_per_beat
            abs_beat = abs_tick / self.ticks_per_beat

            pos.bar = int(abs_beat / self.beats_per_bar)
            pos.beat = int(abs_beat - (pos.bar * self.beats_per_bar) + 1)
            pos.tick = int(abs_tick - (abs_beat * self.ticks_per_beat))
            pos.bar_start_tick = (
                pos.bar * self.beats_per_bar * self.ticks_per_beat)
            pos.bar += 1  # adjust start to bar 1
        else:
            # Compute BBT info based on previous period.
            pos.tick += int(nframes * pos.ticks_per_beat *
                            pos.beats_per_minute / (pos.frame_rate * 60))

            while pos.tick >= pos.ticks_per_beat:
                pos.tick -= int(pos.ticks_per_beat)
                pos.beat += 1

                if pos.beat > pos.beats_per_bar:
                    pos.beat = 1
                    pos.bar += 1
                    pos.bar_start_tick += pos.beats_per_bar * pos.ticks_per_beat

    def become_timebase_master(self):
        return self.set_timebase_callback(self.timebase_callback, True)

    def change_bpm(self, bpm):
        self.bpm = bpm
        self.need_update = True

    def get_bpm(self):
        return self.bpm
