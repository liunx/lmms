#!/usr/bin/env python3
import sys
import time
import socket
import threading
import subprocess
import jack
import mido
from mido import MidiFile
import fluidsynth


def demo01():
    cli = jack.Client('xxx')
    s1 = '../../soundfont/sf2/ChateauGrand-Plus-Instruments-bs16i-v1.4.sf2'
    s2 = "/usr/share/sounds/sf2/FluidR3_GM.sf2"
    fs = fluidsynth.Synth(gain=1.0, samplerate=48000)
    fs2 = fluidsynth.Synth(gain=1.0, samplerate=48000)
    # pulseaudio or jack
    fs.start(driver='jack')
    fs2.start(driver='jack')
    sf = fs.sfload(s1)
    sf2 = fs2.sfload(s2)
    cli.connect('fluidsynth:left', 'system:playback_1')
    cli.connect('fluidsynth:right', 'system:playback_2')
    cli.connect('fluidsynth-01:left', 'system:playback_1')
    cli.connect('fluidsynth-01:right', 'system:playback_2')
    chan1 = 0
    chan2 = 9
    #fs.program_select(chan1, sf, 0, 0)
    #fs2.program_select(chan2, sf2, 0, 0)
    fs.program_change(chan1, 40)
    fs2.program_change(chan2, 0)
    for _ in range(3):
        if 1:
            fs.noteon(chan1, 60, 100)
            fs.noteon(chan1, 64, 100)
            fs.noteon(chan1, 67, 100)
            fs2.noteon(chan2, 60, 100)
            fs2.noteon(chan2, 64, 100)
            fs2.noteon(chan2, 67, 100)
        time.sleep(1.0)
        fs.noteoff(chan1, 60)
        fs.noteoff(chan1, 64)
        fs.noteoff(chan1, 67)
        fs2.noteoff(chan2, 60)
        fs2.noteoff(chan2, 64)
        fs2.noteoff(chan2, 67)
    fs.delete()
    fs2.delete()
    cli.close()


def benchmark(fs, tm):
    t1 = time.time()
    for _ in range(1000):
        for i in range(40, 56):
            fs.noteon(0, i, 10)
        time.sleep(tm)
        for i in range(40, 56):
            fs.noteoff(0, i)
    avg = round((time.time() - t1) / 1000, 4)
    print('avg time cost: {}'.format(avg))


def demo02():
    s1 = '../../soundfont/sf2/ChateauGrand-Plus-Instruments-bs16i-v1.4.sf2'
    fs = fluidsynth.Synth(gain=1.0, samplerate=48000)
    fs.start(driver='jack')
    fs.sfload(s1)
    cli = jack.Client('xxx')
    cli.connect('fluidsynth:left', 'system:playback_1')
    cli.connect('fluidsynth:right', 'system:playback_2')
    fs.program_change(0, 1)
    benchmark(fs, 0.0312)
    fs.delete()
    cli.close()


def demo03():
    seq = fluidsynth.Sequencer(1000)
    for _ in range(20):
        print(seq.get_tick())
        time.sleep(0.001)
    seq.delete()


loop = True


def work_thread(cv, seq, sid):
    with cv:
        cv.wait()
    while True:
        print("hello from work thread {}".format(seq.get_tick()))
        seq.note_on(500, 0, 60, 80, dest=sid)
        time.sleep(0.1)
        if not loop:
            break


def add_synth(sf2, channel=0, program=0, driver='alsa'):
    fs = fluidsynth.Synth(gain=1.0, samplerate=48000)
    fs.start(driver=driver)
    fs.sfload(sf2)
    fs.program_change(channel, program)
    return fs


def demo04():
    global loop
    sf2 = "/usr/share/sounds/sf2/FluidR3_GM.sf2"
    seq = fluidsynth.Sequencer()
    fs1 = add_synth(sf2, program=1)
    fs2 = add_synth(sf2, program=40)
    sid1 = seq.register_fluidsynth(fs1)
    sid2 = seq.register_fluidsynth(fs2)
    cv = threading.Condition()
    t1 = threading.Thread(target=work_thread, args=(cv, seq, sid1))
    t1.start()
    t2 = threading.Thread(target=work_thread, args=(cv, seq, sid2))
    t2.start()
    with cv:
        cv.notify_all()
    time.sleep(10)
    loop = False
    t1.join()
    t2.join()
    fs1.delete()
    fs2.delete()
    seq.delete()

    print('exit!')


def demo05():
    notes = [
        [200, 9, 36, 100],
        [0, 9, 36, 100],
        [200, 9, 40, 100],
        [0, 9, 40, 100],
    ]
    sf2 = "/usr/share/sounds/sf2/FluidR3_GM.sf2"
    fs = add_synth(sf2, program=0, channel=9)
    seq = fluidsynth.Sequencer()
    sid = seq.register_fluidsynth(fs)
    start_tick = seq.get_tick()
    ts = 1 / 1000
    for n in notes * 20:
        _time = n[0]
        curr_tick = seq.get_tick()
        _time -= (curr_tick - start_tick)
        if n[0] == 0:
            seq.note_off(time=0, absolute=False,
                         channel=n[1], key=n[2], dest=sid)
        else:
            seq.note_on(time=_time, absolute=False,
                        channel=n[1], key=n[2], velocity=n[3], dest=sid)
            time.sleep(ts * _time)
        start_tick += n[0]
    time.sleep(1)
    seq.delete()
    fs.delete()


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

    def __del__(self):
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


def demo06():
    seq = Sequencer(driver='jack')
    seq.import_midi('demo.mid')
    seq.import_midi('GM_kit_demo1.mid')
    seq.play(bpm=120)


def demo07():
    seq = Sequencer()
    name = 'calf'
    port = 'Calf Studio Gear:fluidsynth MIDI In'
    mid = seq.load_midi('GM_kit_demo1.mid')
    msgs = seq.merge_tracks(mid)
    seq.add_remote_track(name, port)
    seq.add_messages(name, msgs)
    seq.play(bpm=120)


def demo08():
    seq = Sequencer()
    with mido.open_input() as port:
        for msg in port:
            print(msg)


class Effect:
    def __init__(self, host='localhost', port=10086):
        self.host = host
        self.port = port
        self.proc = subprocess.Popen(["mod-host", "-v", '-p', f'{port}'])
        time.sleep(1)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def __del__(self):
        self.proc.kill()
        self.proc.wait()

    def send(self, data):
        self.sock.connect((self.host, self.port))
        self.sock.send(bytes(data, "utf-8"))
        resp = self.sock.recv(64).decode("utf-8")
        self.sock.close()
        return resp


def demo09():
    effect = Effect()
    for i in range(20):
        s = f'add http://calf.sourceforge.net/plugins/Compressor {i}'
        effect.send(s)
        time.sleep(1)
    time.sleep(10)


def demo10():
    proc = subprocess.Popen(["mod-host", "-i"], stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print(proc.stdout.read())
    proc.kill()


if __name__ == '__main__':
    demo10()
