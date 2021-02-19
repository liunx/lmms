import time
import jack
import numpy as np
import soundfile as sf
import PyWave


class Recorder:
    def __init__(self, filename, channels=2, name='recorder'):
        self.client = jack.Client(name)
        samplerate = self.client.samplerate
        self.wf = PyWave.open(filename, mode='w', channels=channels, frequency=samplerate,
                              bits_per_sample=32, format=PyWave.WAVE_FORMAT_IEEE_FLOAT)

        for i in range(channels):
            self.client.inports.register(f'in_{i}')
        self.client.set_process_callback(self.process)
        self.client.set_sync_callback(self.sync)
        self.client.activate()
        self.channels = channels
        self.is_start = False

    def connect(self, ports):
        for s, d in zip(ports, self.client.inports):
            self.client.connect(s, d)

    def process(self, frames):
        assert frames == self.client.blocksize
        if self.is_start:
            l = []
            for p in self.client.inports:
                l.append(p.get_array())
            _data = np.vstack(l)
            _data = _data.transpose()
            self.wf.write(_data.tostring())

    def sync(self, state, pos):
        return True

    def start(self):
        self.is_start = True

    def stop(self):
        self.is_start = False

    def close(self):
        self.client.close()
        self.wf.close()


class Player:
    def __init__(self, filename, channels=2, name='player'):
        self.index = 0
        self.client = jack.Client(name)
        for i in range(channels):
            self.client.outports.register(f'out_{i}')
        self.channels = channels
        self.is_start = False
        blocksize = self.client.blocksize
        with sf.SoundFile(filename) as f:
            block_generator = f.blocks(blocksize=blocksize, dtype='float32',
                                       always_2d=True, fill_value=0)
            self.blocks = [b for b in block_generator]
            self.blocks_len = len(self.blocks)
        self.client.set_process_callback(self.process)
        self.client.set_sync_callback(self.sync)
        self.client.activate()

    def close(self):
        self.client.close()

    def connect(self, ports):
        for s, d in zip(self.client.outports, ports):
            self.client.connect(s, d)

    def process(self, frames):
        assert frames == self.client.blocksize
        if self.index > self.blocks_len - 1:
            for port in self.client.outports:
                port.get_array().fill(0)
            self.is_start = False
        if self.is_start:
            data = self.blocks[self.index]
            self.index += 1
            for channel, port in zip(data.T, self.client.outports):
                port.get_array()[:] = channel

    def sync(self, state, pos):
        return True

    def start(self):
        self.is_start = True

    def stop(self):
        self.is_start = False


def demo01():
    rec = Recorder('rec.wav')
    rec.connect(['work:left', 'work:right'])
    rec.rec()
    time.sleep(20)
    rec.stop()
    rec.close()


def demo02():
    player = Player('tests/xxx.wav')
    player.connect(['system:playback_1', 'system:playback_2'])
    player.start()
    time.sleep(24)
    player.close()


if __name__ == '__main__':
    demo02()
