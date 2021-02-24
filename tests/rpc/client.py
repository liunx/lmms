import timeit
import time
import xmlrpc.client


def load_midi(s, name, filename):
    with open(filename, 'rb') as f:
        t = timeit.default_timer()
        s.load_midi(name, xmlrpc.client.Binary(f.read()))
        print(timeit.default_timer() - t)


def load_audio(s, name, filename):
    with open(filename, 'rb') as f:
        t = timeit.default_timer()
        s.load_audio(name, xmlrpc.client.Binary(f.read()))
        print(timeit.default_timer() - t)


if __name__ == '__main__':
    s = xmlrpc.client.ServerProxy('http://localhost:8000')
    # s.add_synth('synth_01')
    s.add_seq('seq')
    s.play(90)
    time.sleep(10)
    s.stop()
