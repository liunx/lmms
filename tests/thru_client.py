#!/usr/bin/env python3

"""Create a JACK client that copies input audio directly to the outputs.

This is somewhat modeled after the "thru_client.c" example of JACK 2:
http://github.com/jackaudio/jack2/blob/master/example-clients/thru_client.c

If you have a microphone and loudspeakers connected, this might cause an
acoustical feedback!

"""
import sys
import signal
import os
import jack
import wave
import numpy as np
import threading
import PyWave
from scipy.io.wavfile import write

if sys.version_info < (3, 0):
    # In Python 2.x, event.wait() cannot be interrupted with Ctrl+C.
    # Therefore, we disable the whole KeyboardInterrupt mechanism.
    # This will not close the JACK client properly, but at least we can
    # use Ctrl+C.
    signal.signal(signal.SIGINT, signal.SIG_DFL)
else:
    # If you use Python 3.x, everything is fine.
    pass

argv = iter(sys.argv)
# By default, use script name without extension as client name:
defaultclientname = os.path.splitext(os.path.basename(next(argv)))[0]
clientname = next(argv, defaultclientname)
servername = next(argv, None)

wf = PyWave.open('pywave.wav', mode='w', channels=2, frequency=48000,
                 bits_per_sample=32, format=PyWave.WAVE_FORMAT_IEEE_FLOAT)

client = jack.Client(clientname, servername=servername)

if client.status.server_started:
    print('JACK server started')
if client.status.name_not_unique:
    print('unique name {0!r} assigned'.format(client.name))

event = threading.Event()


@client.set_process_callback
def process(frames):
    assert len(client.inports) == len(client.outports)
    assert frames == client.blocksize
    data = client.inports[0].get_array()
    # [[ch1, ch2], [ch1, ch2]...]
    _data = np.vstack([data, data])
    _data = _data.transpose()
    wf.write(_data.tostring())
    for i, o in zip(client.inports, client.outports):
        o.get_buffer()[:] = i.get_buffer()


@client.set_shutdown_callback
def shutdown(status, reason):
    print('JACK shutdown!')
    print('status:', status)
    print('reason:', reason)
    event.set()


# create two port pairs
for number in 1, 2:
    client.inports.register('input_{0}'.format(number))
    client.outports.register('output_{0}'.format(number))

with client:
    # When entering this with-statement, client.activate() is called.
    # This tells the JACK server that we are ready to roll.
    # Our process() callback will start running now.

    # Connect the ports.  You can't do this before the client is activated,
    # because we can't make connections to clients that aren't running.
    # Note the confusing (but necessary) orientation of the driver backend
    # ports: playback ports are "input" to the backend, and capture ports
    # are "output" from it.

    capture = client.get_ports(is_physical=True, is_output=True)
    if not capture:
        raise RuntimeError('No physical capture ports')

    caport = 'CODEC,0,0-in:capture_1'
    client.connect(caport, client.inports[0])
    client.connect(caport, client.inports[1])

    playback = client.get_ports(is_physical=True, is_input=True)
    if not playback:
        raise RuntimeError('No physical playback ports')

    for src, dest in zip(client.outports, ['CODEC,0,0-out:playback_1', 'CODEC,0,0-out:playback_2']):
        client.connect(src, dest)

    print('Press Ctrl+C to stop')
    try:
        event.wait()
    except KeyboardInterrupt:
        print('\nInterrupted by user')

# When the above with-statement is left (either because the end of the
# code block is reached, or because an exception was raised inside),
# client.deactivate() and client.close() are called automatically.
wf.close()
