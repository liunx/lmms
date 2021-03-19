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
        self.pos = 0
        self.bpm = 90
        self.bpm_rate = Fraction(1, 1)
        self.msgs = {}
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

    def seek_msgs(self, pos):
        idx = bisect_left(self.msgs_keys, pos)
        _pos = self.msgs_keys[idx]

    def time_to_frames(self, time_):
        time_per_beat = Fraction(60, self.bpm)
        frames_per_beat = time_per_beat / self.time_per_frame
        rate = Fraction(time_, self.mid.ticks_per_beat)
        frames = frames_per_beat * rate
        return round(frames)

    def process(self, frames):
        stat = self.cli.transport_state
        if stat == jack.STOPPED:
            return
        # follow transport_frame
        self.midi_port.clear_buffer()
        if stat == jack.STARTING or stat == jack.ROLLING:
            start_pos = self.cli.transport_frame
            i = 0
            while i < frames:
                offset = start_pos + i
                if offset in self.msgs_keys:
                    msgs = self.msgs[offset]
                    for msg in msgs:
                        self.midi_port.write_midi_event(i, msg.bytes())
                i += 1

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
        self.debug = debug
        self.ticks_per_beat = ticks_per_beat
        self.stop_event = Event()
        self.set_shutdown_callback(self.shutdown_callback)

    def shutdown_callback(self, status, reason):
        print('JACK shutdown:', reason, status)
        self.stop_event.set()

    def timebase_callback(self, state, nframes, pos, new_pos):
        if new_pos:
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
            assert pos.valid & jack.POSITION_BBT
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


class Sequencer2:
    sf2 = "/usr/share/sounds/sf2/FluidR3_GM.sf2"

    def __init__(self, driver='jack', time_scale=1024, samplerate=48000):
        self.synths = []
        self.output_ports = []
        self.tracks = {}
        self.track_len = 0
        self.cv = threading.Condition()
        self.seq = fluidsynth.Sequencer(time_scale)
        self.ticks_per_beat = time_scale
        self.driver = driver
        self.samplerate = samplerate
        if driver == 'alsa':
            mido.set_backend('mido.backends.rtmidi/LINUX_ALSA')
        elif driver == 'jack':
            mido.set_backend('mido.backends.rtmidi/UNIX_JACK')
        else:
            raise ValueError(f'Unsupported driver {driver}!')

    def close(self):
        self.seq.delete()
        for s in self.synths:
            s.delete()
        for p in self.output_ports:
            p.close()

    def add_local_track(self, name, sf2=None, channel=0, program=0, gain=1.0):
        fs = fluidsynth.Synth(gain, self.samplerate)
        if self.driver == 'jack':
            fs.setting('midi.driver', 'jack')
            fs.setting('audio.jack.id', name)
            fs.setting('audio.jack.autoconnect', False)
        fs.start(driver=self.driver)
        if not sf2:
            fs.sfload(self.sf2)
        else:
            fs.sfload(sf2)
        fs.program_change(channel, program)
        self.synths.append(fs)
        if name in self.tracks:
            raise ValueError(f'track {name} already exist!')
        self.tracks[name] = {'type': 'local',
                             'fluidsynth': fs,  'messages': []}

    def add_remote_track(self, name, port, gain=1.0):
        fs = mido.open_output(port)
        self.tracks[name] = {'type': 'remote',
                             'fluidsynth': fs,  'messages': []}

    def add_messages(self, track_name, msgs):
        if track_name not in self.tracks:
            raise ValueError(f'track {track_name} not exist!')
        self.tracks[track_name]['messages'] = msgs

    def send_local_msg(self, fs, msg):
        if msg.type == 'program_change':
            fs.program_change(msg.channel, msg.program)
        elif msg.type == 'note_off':
            fs.noteoff(msg.channel, msg.note)
        elif msg.type == 'note_on':
            fs.noteon(msg.channel, msg.note, msg.velocity)

    def send_remote_msg(self, fs, msg):
        fs.send(msg)

    def track_thread(self, track):
        with self.cv:
            self.cv.wait()
        tp = track['type']
        fs = track['fluidsynth']
        msgs = track['messages']
        start_tick = self.start_tick
        for msg in msgs:
            if not self.run:
                break
            _time = msg.time
            time.sleep(self.tick_to_second * _time)
            if tp == 'local':
                self.send_local_msg(fs, msg)
            elif tp == 'remote':
                self.send_remote_msg(fs, msg)
            else:
                raise ValueError(f'Unsupported type {tp}!')
            start_tick += msg.time

    def update_mid_time(self, mid):
        if self.ticks_per_beat == mid.ticks_per_beat:
            return mid
        for track in mid.tracks:
            for msg in track:
                if msg.time > 0:
                    msg.time = int(self.ticks_per_beat *
                                   msg.time / mid.ticks_per_beat)
        return mid

    def load_midi(self, filename):
        mid = MidiFile(filename)
        mid = self.update_mid_time(mid)
        return mid

    def merge_tracks(self, mid):
        return mido.merge_tracks(mid.tracks)

    def import_midi(self, filename, sf2=None):
        mid = self.load_midi(filename)
        i = 1
        for track in mid.tracks:
            _name = filename + f'track{i}'
            i += 1
            _channel = 0
            for msg in track:
                if msg.is_meta and msg.type == 'track_name':
                    _name = msg.name
                elif msg.type == 'note_on':
                    # avoid no program change event
                    _channel = msg.channel
                    break
            self.add_local_track(_name, channel=_channel, sf2=sf2)
            self.add_messages(_name, track)

    def play(self, bpm=90):
        self.run = True
        threads = []
        tempo = mido.bpm2tempo(bpm)
        self.tick_to_second = mido.tick2second(1, self.ticks_per_beat, tempo)
        for k, v in self.tracks.items():
            t = threading.Thread(target=self.track_thread, name=k, args=([v]))
            t.start()
            threads.append(t)
        self.start_tick = self.seq.get_tick()
        with self.cv:
            self.cv.notify_all()
        #self.run = False
        for t in threads:
            t.join()
        print('complete!')
