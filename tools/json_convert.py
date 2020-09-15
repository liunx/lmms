#!/usr/bin/env python3
import sys
import json

def demo01():
    with open(sys.argv[1]) as f:
        data = json.load(f)
    inst = data['instruments']
    i = 0
    d = {}
    # name, channel, program, lownotes, highnotes
    for k, v in inst.items():
        n = v.replace(' ', '')
        d[n] = [v, 0, i, 0, 0]
        i += 1
    perc =  data['percussion']
    i = 34
    for k, v in perc.items():
        n = v.replace(' ', '')
        d[n] = [v, 10, i, 0, 0]
        i += 1
    with open(sys.argv[2], 'w') as f:
        json.dump(d, f)

def demo02():
    data = {}
    outdata = {}
    d = {
        "preset": "data/presets/Sf2Player/default.xpf",
        "name": "",
        "plugin": "Sf2Player",
        "src": "/usr/share/sounds/sf2/FluidR3_GM.sf2",
        "patch": 0,
        "beats": False
    }
    with open(sys.argv[1]) as f:
        data = json.load(f)
    for k, v in data.items():
        d['name'] = v[0]
        d['patch'] = str(v[2])
        if v[1] == 10:
            d['beats'] = True
        outdata[k] = dict(d)
    with open(sys.argv[2], 'w') as f:
        json.dump(outdata, f)


if __name__ == "__main__":
    demo02()