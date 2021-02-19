import time
import threading
import fluidsynth
import mido
from mido import MidiFile


class Sequencer:
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
            fs.setting('audio.jack.id', name)
            fs.setting('audio.jack.autoconnect', True)
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
