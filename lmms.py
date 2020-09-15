#!/usr/bin/env python3

import sys
import re
import json
from os import path
from lxml import etree


class AudioFileProcessor:
    def __init__(self, inst):
        tree = etree.parse(inst.preset)
        pt = tree.xpath('/lmms-project/instrumenttracksettings')[0]
        pt.tag = 'track'
        pt.attrib['name'] = inst.name
        elem = pt.xpath('instrumenttrack/instrument/audiofileprocessor')[0]
        elem.attrib['src'] = inst.src
        self.presettrack = pt

    def track(self):
        return self.presettrack

    def setparam(self, param):
        pass

    def getparam(self):
        pass


class Sf2Player:
    params = {}
    def __init__(self, inst):
        tree = etree.parse(inst.preset)
        pt = tree.xpath('/lmms-project/instrumenttracksettings')[0]
        pt.tag = 'track'
        pt.attrib['name'] = inst.name
        elem = pt.xpath('instrumenttrack/instrument/sf2player')[0]
        elem.attrib['src'] = inst.src
        elem.attrib['patch'] = inst.patch
        self.presettrack = pt

    def track(self):
        return self.presettrack

    def setparam(self, param):
        pass

    def getparam(self):
        pass


class Kicker:
    def __init__(self, inst):
        tree = etree.parse(inst.preset)
        pt = tree.xpath('/lmms-project/instrumenttracksettings')[0]
        pt.tag = 'track'
        pt.attrib['name'] = inst.name
        self.presettrack = pt

    def track(self):
        return self.presettrack

    def setparam(self, param):
        pass

    def getparam(self):
        pass


class Lmms:
    presets = {}
    unit = 12
    steps = 16
    beattracks = 1

    def __init__(self, project):
        self.project = etree.parse(project)

    def write(self, file):
        self.project.write(file, encoding='utf-8', xml_declaration=True)

    def collectpresets(self, file):
        with open(file) as f:
            for l in f:
                l = l.strip()
                s = re.sub('.*data/presets/', '', l)
                s = re.sub('(.xpf|.xiz)', '', s)
                nm = re.sub('/', '.', s)
                absp = path.abspath(l)
                self.presets[nm] = absp

    def listpresets(self):
        return list(self.presets.keys())

    def addpreset(self, track, preset):
        tree = etree.parse(self.presets.get(preset))
        pt = tree.xpath(
            '/lmms-project/instrumenttracksettings/instrumenttrack')[0]
        track.append(pt)
        return pt

    def addbeatpreset(self, preset, name):
        tracks = self.project.xpath('/lmms-project/song/trackcontainer/track[@type="1"]')
        self.beattracks = len(tracks)
        track = tracks[0]
        t = track.xpath('bbtrack/trackcontainer')[0]
        tree = etree.parse(self.presets.get(preset))
        pt = tree.xpath('/lmms-project/instrumenttracksettings')[0]
        pt.tag = 'track'
        pt.attrib['name'] = name
        t.append(pt)
        return pt

    def addtrack(self, name):
        parent = self.project.xpath('/lmms-project/song/trackcontainer')[0]
        parent.append(track)
        return track

    def addbeatinstrument(self, inst):
        track = self.project.xpath('/lmms-project/song/trackcontainer/track[@type="1"]')[0]
        subtrack = track.xpath('bbtrack/trackcontainer')[0]
        subtrack.append(inst)
        return pt

    def findtrack(self, name):
        track = self.project.xpath(
            '/lmms-project/song/trackcontainer/track[@name="{}"]'.format(name))[0]
        return track

    def _addpattern(self, track, _type, pos):
        pattern = etree.Element('pattern', pos=pos, muted='0', steps='16')
        pattern.attrib['name'] = track.attrib['name']
        pattern.attrib['type'] = _type
        track.append(pattern)
        return pattern

    def addpattern(self, track):
        return self._addpattern(track, '1', '0')

    def addbeatpattern(self, track):
        pos = 0
        for i in range(self.beattracks):
            self._addpattern(track, '0', str(int(pos)))
            pos = pos + self.steps * self.unit

    def _addbeatpattern(self, track):
        pos = self.steps * self.unit * (self.beattracks - 1)
        return self._addpattern(track, '0', str(int(pos)))

    def addnotes(self, pattern, notes, pos, pitch, vol):
        offset = self.steps * self.unit * pos
        for n in notes:
            if n['type'] == 'Note':
                elem = etree.Element('note', key="0", pan="0", len="0", vol="0", pos="0")
                elem.attrib['key'] = str(n['key'] + pitch)
                elem.attrib['pos'] = str(int(offset + self.unit * n['pos'] * 4))
                elem.attrib['len'] = str(int(self.unit * n['len'] * 4))
                elem.attrib['vol'] = str(vol * 10)
                pattern.append(elem)
            elif n['type'] == 'Chord':
                for k in n['keys']:
                    elem = etree.Element('note', key="0", pan="0", len="0", vol="140", pos="0")
                    elem.attrib['key'] = str(k + pitch)
                    elem.attrib['pos'] = str(int(offset + self.unit * n['pos'] * 4))
                    elem.attrib['len'] = str(int(self.unit * n['len'] * 4))
                    pattern.append(elem)
            elif n['type'] == 'Measure':
                offset = offset + (self.unit * self.steps)

    def addbeatnotes(self, pattern, notes):
        offset = 0
        for n in notes:
            if n == '1':
                elem = etree.Element('note', pos="0", len="-192", key="57", vol="100", pan="0")
                elem.attrib['pos'] = str(int(offset))
                pattern.append(elem)
            offset = offset + self.unit

    def _addbbtrack(self, track):
        t = etree.Element('bbtrack')
        #self._addbbtrackcontainer(t)
        track.append(t)

    def _addbbtrackcontainer(self, track):
        t = etree.Element('trackcontainer', width="640", x="610", y="5", maximized="0",
                          height="400", visible="0", type="bbtrackcontainer", minimized="0")
        track.append(t)

    def addbeattrack(self, name):
        parent = self.project.xpath('/lmms-project/song/trackcontainer')[0]
        track = etree.Element(
            'track', type='1', name=name, muted='0', solo='0')
        self._addbbtrack(track)
        parent.append(track)
        return track

    def findbeattrack(self, name):
        track = self.project.xpath(
            '/lmms-project/song/trackcontainer/track[@name="{}"]'.format(name))[0]
        return track

    def addbbtco(self, track, offset, count):
        for i in range(count):
            pos = str((i + offset) * self.unit * self.steps)
            bbtco = etree.Element(
                'bbtco', color="4286611584", pos=pos, name="", muted="0", len="192", usestyle="1")
            track.append(bbtco)

    def addautomationtrack(self, name):
        pass

    def findautomationtrack(self, name):
        pass

    def addautomationpattern(self, name):
        pass

    def findautomationpattern(self, name):
        pass

    def removetrack(self, track):
        root = self.project.getroot()
        root.remove(track)

    def changesteps(self, track, steps):
        self.steps = steps
        pass

    def muted(self, track, val):
        track.attrib['muted'] = str(val)

    def changebpm(self, bpm):
        head = self.project.xpath('/lmms-project/head')[0]
        head.attrib['bpm'] = str(bpm)

    def changevol(self, vol):
        head = self.project.xpath('/lmms-project/head')[0]
        head.attrib['mastervol'] = str(vol)

    def changepitch(self, pitch):
        head = self.project.xpath('/lmms-project/head')[0]
        head.attrib['masterpitch'] = str(pitch)

    def getbeatpattern(self, beattrack, presettrack):
        tracks =  self.project.xpath('/lmms-project/song/trackcontainer/track[@type="1"]')
        index = tracks.index(beattrack)
        patterns = presettrack.xpath('pattern')
        return patterns[index]

    def getdefaultbeattrack(self):
        return self.project.xpath('/lmms-project/song/trackcontainer/track[@type="1"]')[0]

    def _updatebeatpatterns(self):
        dftrack = self.getdefaultbeattrack()
        tracks = dftrack.xpath('bbtrack/trackcontainer/track')
        pt = []
        for track in tracks:
            pt.append(self._addbeatpattern(track))
        return pt

    def addbeatbaseline(self, name):
        parent = self.project.xpath('/lmms-project/song/trackcontainer')[0]
        track = etree.Element('track', type='1', name=name, muted='0', solo='0')
        self._addbbtrack(track)
        parent.append(track)
        self.beattracks = self.beattracks + 1
        # update patterns
        patterns = self._updatebeatpatterns()
        return (track, patterns)

    def addinstrument(self, inst):
        plug = None
        if inst.plugin == 'Sf2Player':
            plug = Sf2Player(inst)
        elif inst.plugin == 'AudioFileProcessor':
            plug = AudioFileProcessor(inst)
        elif inst.plugin == 'Kicker':
            plug = Kicker(inst)
        attrib = {}
        track = plug.track()
        if inst.beats:
            parent = self.project.xpath('/lmms-project/song/trackcontainer/track/bbtrack/trackcontainer')[0]
            pattern = self.addbeatpattern(track)
        else:
            parent = self.project.xpath('/lmms-project/song/trackcontainer')[0]
            pattern = self.addpattern(track)
        parent.append(track)
        attrib['track'] = track
        attrib['pattern'] = pattern
        return attrib

    def addpreset(self, preset):
        pass

    def addsample(self, sample):
        pass

