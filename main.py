#!/usr/bin/env python3
from lmms import Lmms
from composer import Composer
import json
import sys


_volumes = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9',
                     'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k',
                     'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v',
                     'w', 'x', 'y', 'z']

class Struct:
    def __init__(self, **args):
        self.__dict__.update(args)


class Runner:
    band = {}
    bandinfo = {}
    instruments = {}
    melody = {}
    rhythm = {}
    beats = {}
    beatsbaselines = {}
    tracks = {}
    def __init__(self):
        proj = 'data/projects/templates/default.mpt'
        presets = 'data/presets.txt'
        with open('data/instruments.json') as f:
            self.instruments = json.load(f)
        self.lmms = Lmms(proj)
        self.lmms.collectpresets(presets)
        self.comp = Composer()

    def addinstrument(self, instru, name):
        plug = self.instruments[instru]
        inst = Struct(**plug)
        inst.name = name
        attrib = self.lmms.addinstrument(inst)
        self.band[name] = attrib

    def addbeatbaseline(self, name):
        track, patterns = self.lmms.addbeatbaseline(name)
        self.band[name] = (track, patterns)

    def addbeatmeasures(self, name, pos, count):
        track = self.band[name][0]
        self.lmms.addbbtco(track, pos, count)

    def addnotes(self, name, notes, pos, pitch, vol):
        attrib = self.band[name]
        self.lmms.addnotes(attrib['pattern'], notes, pos, pitch, vol)

    def addbeats(self, name, drumkit, beats):
        tmap = {}
        patterns = self.band[name][1]
        for p in patterns:
            if p.attrib['name'] in drumkit:
                tmap[p.attrib['name']] = p
        i = 0
        for n in drumkit:
            p = tmap[n]
            s = beats[i]
            _beats = s.replace('_', '')
            self.lmms.addbeatnotes(p, _beats)
            i = i + 1

    def mastercontrol(self, bpm=100, vol=100, pitch=0):
        self.lmms.changebpm(bpm)

    def saveproject(self, name):
        self.lmms.write(name)

    def instrumenttrack(self, name, clip, track, pitch):
        pos = 0
        m, n = clip.split(':')
        while pos < len(track):
            idx = _volumes.index(track[pos])
            if idx > 0:
                if m == 'melody':
                    _len, notes = self.melody[n]
                    self.addnotes(name, notes, pos, pitch, idx)
                    pos = pos + _len
                elif m == 'rhythm':
                    _len, notes = self.rhythm[n]
                    self.addnotes(name, notes, pos, pitch, idx)
                    pos = pos + _len
            else:
                pos = pos + 1

    def beatsbaselinetrack(self, name, track, pattern):
        pos = 0
        drumkit = self.beatsbaselines[name]
        m, n = pattern.split(':')
        beats = self.beats[n]
        self.addbeats(name, drumkit, beats)
        for l in track:
            if l == '1':
                self.addbeatmeasures(name, pos, 1)
            pos = pos + 1

    def loadband(self, jsonfile):
        with open(jsonfile) as f:
            self.bandinfo = json.load(f)
        self.mastercontrol(bpm=self.bandinfo['bpm'])
        instruments = self.bandinfo['instruments']
        for n, p in instruments.items():
            self.addinstrument(p, n)
        self.beatsbaselines = self.bandinfo['beatsbaselines']
        for k in self.beatsbaselines.keys():
            self.addbeatbaseline(k)
        melody = self.bandinfo['melody']
        for k,v in melody.items():
            _len, notes = self.comp.tonotation(v[1])
            self.melody[k] = [_len, notes]
        rhythm = self.bandinfo['rhythm']
        for k,v in rhythm.items():
            _len, notes = self.comp.tonotation(v[1])
            self.rhythm[k] = [_len, notes]
        self.beats = self.bandinfo['beats']
        # add tracks
        for track in self.bandinfo['tracks']:
            _id = track['id']
            self.tracks[_id] = track
        # load song
        self.loadsong(self.bandinfo['song'])

    def addtrack(self, track, measures):
        refer = track['refer']
        clip = track['clip']
        pitch = track['pitch']
        m, n =  refer.split(':')
        if m == 'instruments':
            self.instrumenttrack(n, clip, measures, pitch)
        elif m == 'beatsbaselines':
            pattern = track['pattern']
            self.beatsbaselinetrack(n, measures, pattern)

    def loadsong(self, song):
        self.mastercontrol(bpm=song['bpm'])
        for track in song['tracks']:
            track = track.replace('_', '')
            _id, m = track.split(':')
            _id = int(_id)
            track = self.tracks[_id]
            self.addtrack(track, m)


def lmms(song, filename):
    runner = Runner()
    runner.loadband(song)
    runner.saveproject(filename)


if __name__ == "__main__":
    song = sys.argv[1]
    filename = song.replace('json', 'mmp')
    lmms(song, filename)