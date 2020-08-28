#!/usr/bin/env python3
import sys
import json
import re
import argparse
import subprocess
from os import path
from music21 import *


InstrumentMap = {
    'Accordion': instrument.Accordion,    
    'AcousticBass': instrument.AcousticBass,            
    'AcousticGuitar': instrument.AcousticGuitar,
    'Agogo': instrument.Agogo,          
    'Alto': instrument.Alto,  
    'AltoSaxophone': instrument.AltoSaxophone,
    'Bagpipes': instrument.Bagpipes,    
    'Banjo': instrument.Banjo,                        
    'Baritone': instrument.Baritone,
    'BaritoneSaxophone': instrument.BaritoneSaxophone,
    'Bass': instrument.Bass,          
    'BassClarinet': instrument.BassClarinet,
    'BassDrum': instrument.BassDrum,              
    'BassTrombone': instrument.BassTrombone,  
    'Bassoon': instrument.Bassoon,      
    'BongoDrums': instrument.BongoDrums,              
    'BrassInstrument': instrument.BrassInstrument,
    'Castanets': instrument.Castanets,
    'Celesta': instrument.Celesta,                      
    'ChurchBells': instrument.ChurchBells,                
    'Clarinet': instrument.Clarinet,        
    'Clavichord': instrument.Clavichord,  
    'CongaDrum': instrument.CongaDrum,  
    'Contrabass': instrument.Contrabass,                              
    'Cowbell': instrument.Cowbell,            
    'CrashCymbals': instrument.CrashCymbals,                  
    'Cymbals': instrument.Cymbals,                  
    'Dulcimer': instrument.Dulcimer,              
    'ElectricBass': instrument.ElectricBass,              
    'ElectricGuitar': instrument.ElectricGuitar,
    'ElectricOrgan': instrument.ElectricOrgan,
    'EnglishHorn': instrument.EnglishHorn,
    'FingerCymbals': instrument.FingerCymbals,
    'Flute': instrument.Flute,
    'FretlessBass': instrument.FretlessBass,
    'Glockenspiel': instrument.Glockenspiel,
    'Gong': instrument.Gong,
    'Guitar': instrument.Guitar,
    'Handbells': instrument.Handbells,
    'Harmonica': instrument.Harmonica,
    'Harp': instrument.Harp,
    'Harpsichord': instrument.Harpsichord,
    'HiHatCymbal': instrument.HiHatCymbal,
    'Horn': instrument.Horn,
    'Kalimba': instrument.Kalimba,
    'KeyboardInstrument': instrument.KeyboardInstrument,
    'Koto': instrument.Koto,
    'Lute': instrument.Lute,
    'Mandolin': instrument.Mandolin,
    'Maracas': instrument.Maracas,
    'Marimba': instrument.Marimba,
    'MezzoSoprano': instrument.MezzoSoprano,
    'Oboe': instrument.Oboe,
    'Ocarina': instrument.Ocarina,
    'Organ': instrument.Organ,
    'PanFlute': instrument.PanFlute,
    'Percussion': instrument.Percussion,
    'Piano': instrument.Piano,
    'Piccolo': instrument.Piccolo,
    'PipeOrgan': instrument.PipeOrgan,
    'PitchedPercussion': instrument.PitchedPercussion,
    'Ratchet': instrument.Ratchet,
    'Recorder': instrument.Recorder,
    'ReedOrgan': instrument.ReedOrgan,
    'RideCymbals': instrument.RideCymbals,
    'SandpaperBlocks': instrument.SandpaperBlocks,
    'Saxophone': instrument.Saxophone,
    'Shakuhachi': instrument.Shakuhachi,
    'Shamisen': instrument.Shamisen,
    'Shehnai': instrument.Shehnai,
    'Siren': instrument.Siren,
    'Sitar': instrument.Sitar,
    'SizzleCymbal': instrument.SizzleCymbal,
    'SleighBells': instrument.SleighBells,
    'SnareDrum': instrument.SnareDrum,
    'Soprano': instrument.Soprano,
    'SopranoSaxophone': instrument.SopranoSaxophone,
    'SplashCymbals': instrument.SplashCymbals,
    'SteelDrum': instrument.SteelDrum,
    'StringInstrument': instrument.StringInstrument,
    'SuspendedCymbal': instrument.SuspendedCymbal,
    'Taiko': instrument.Taiko,
    'TamTam': instrument.TamTam,
    'Tambourine': instrument.Tambourine,
    'TempleBlock': instrument.TempleBlock,
    'Tenor': instrument.Tenor,
    'TenorDrum': instrument.TenorDrum,
    'TenorSaxophone': instrument.TenorSaxophone,
    'Test': instrument.Test,
    'TestExternal': instrument.TestExternal,
    'Timbales': instrument.Timbales,
    'Timpani': instrument.Timpani,
    'TomTom': instrument.TomTom,
    'Triangle': instrument.Triangle,
    'Trombone': instrument.Trombone,
    'Trumpet': instrument.Trumpet,
    'Tuba': instrument.Tuba,
    'TubularBells': instrument.TubularBells,
    'Ukulele': instrument.Ukulele,
    'UnpitchedPercussion': instrument.UnpitchedPercussion,
    'Vibraphone': instrument.Vibraphone,
    'Vibraslap': instrument.Vibraslap,
    'Viola': instrument.Viola,
    'Violin': instrument.Violin,
    'Violoncello': instrument.Violoncello,
    'Vocalist': instrument.Vocalist,
    'Whip': instrument.Whip,
    'Whistle': instrument.Whistle,
    'WindMachine': instrument.WindMachine,
    'Woodblock': instrument.Woodblock,
    'WoodwindInstrument': instrument.WoodwindInstrument,
    'Xylophone': instrument.Xylophone,
}


class ChordState(tinyNotation.State):
    def affectTokenAfterParse(self, n):
        super(ChordState, self).affectTokenAfterParse(n)
        return None  # do not append Note object

    def end(self):
        ch = chord.Chord(self.affectedTokens)
        ch.duration = self.affectedTokens[0].duration
        return ch


class Notation:
    song = {}
    tracks = {}
    macros = {}
    groups = {}
    istracking = False
    ismacro = False
    isgroup = False
    trackoffset = 0
    def __init__(self, args):
        self.song['title'] = 0
        self.song['tempo'] = 0
        self.song['ts'] = 0
        self.basename = path.basename(args.filepath[0]).replace('.cbd', '')
        self.args = args

    def setparam(self, _type, _val):
        self.song[_type] = _val

    def fillrest(self, notation, distance):
        cn = ''
        num, den = self.song['ts'].split('/')
        num = int(num)
        d = int(distance / num)
        if d > 0:
            cn = notation + ' r1 ' * d
        m = int(distance % num)
        if m > 0:
            cn = notation + ' r4 ' * m
        return cn

    def addtrack(self, shortname, notation):
        track = self.tracks.get(shortname)
        # current notation
        cn = track[4]
        p = self.tostream(cn)
        flat = p.flat
        # current pos
        cp = flat[-1].offset
        if cp < self.trackoffset:
            dist = self.trackoffset - cp
            cn = self.fillrest(cn, dist)
        track[4] = "{} {}".format(cn, notation)

    def updateoffset(self):
        offset = 0
        for v in self.tracks.values():
            p = self.tostream(v[4])
            f = p.flat
            if f[-1].offset > offset:
                offset = f[-1].offset
        self.trackoffset = offset

    def parser(self, lines):
        for l in lines:
            l = l.strip()
            if l:
                if l.startswith('#'):
                    continue
                if l.startswith('@start'):
                    self.istracking = True
                    continue
                if l.startswith('@end'):
                    self.istracking = False
                    continue 
                if l.startswith('@macro_start'):
                    self.ismacro = True
                    continue
                if l.startswith('@macro_end'):
                    self.ismacro = False
                    continue 
                if l.startswith('@group_start'):
                    self.isgroup = True
                    continue
                if l.startswith('@group_end'):
                    self.isgroup = False
                    continue 
                if l.startswith('@instrument_start'):
                    self.iscontroller = True
                    continue
                if l.startswith('@instrument_end'):
                    self.iscontroller = False
                    continue 
                if l.startswith('>>') and self.istracking:
                    self.updateoffset()
                    continue
                if l.find(':') > 0:
                    k, v = l.split(':')
                    k = k.strip()
                    if k in self.song.keys():
                        v = v.strip()
                        self.setparam(k, v)
                elif l.find('=') > 0 and self.iscontroller:
                    shortname, v = l.split('=')
                    fullname, instrument, pitch, muted = v.split(',')
                    self.tracks[shortname.strip()] = [
                        fullname.strip(), instrument.strip(),
                        pitch.strip(),
                        muted.strip(),
                        "tinyNotation: {} ".format(self.song['ts'])]
                elif l.find('=') > 0 and self.isgroup:
                    shortname, v = l.split('=')
                    l = []
                    for i in v.split(','):
                        l.append(i.strip())
                    self.groups[shortname.strip()] = l
                elif l.find('+>') > 0 and self.istracking and not self.ismacro:
                    shortname, notation = l.split('+>')
                    notation = notation.replace('|', ' ')
                    macros = re.findall('[0-9a-zA-Z]+', notation)
                    s = ''
                    for m in macros:
                        s = '{} {}'.format(s, self.macro2notation(m))
                    self.addtrack(shortname.strip(), s)
                elif l.find('->') > 0 and self.istracking and not self.ismacro:
                    shortname, notation = l.split('->')
                    notation = notation.replace('|', ' ')
                    sn = shortname.strip()
                    nt = notation.strip()
                    if sn in self.tracks:
                        self.addtrack(sn, nt)
                    elif sn in self.groups:
                        group = self.groups[sn]
                        for i in group:
                            self.addtrack(i, nt)
                elif l.find('->') > 0 and not self.istracking and self.ismacro:
                    name, notation = l.split('->')
                    notation = notation.replace('|', ' ')
                    self.macros[name] = notation

    def macro2notation(self, macro):
        return self.macros[macro]

    def tostream(self, notation):
        tnc = tinyNotation.Converter(notation)
        tnc.bracketStateMapping['chord'] = ChordState
        return tnc.parse().stream

    def process(self):
        staff = stream.Stream()
        for k, v in self.tracks.items():
            if v[3] == 'T':
                continue
            p = self.tostream(v[4])
            #p.partName = v[0]
            inst = InstrumentMap.get(v[1])
            p.insert(0, inst())
            staff.append(p)
            p.transpose(int(v[2]), inPlace=True)
        self.staff = staff

    def play(self):
        midfile = 'midi/{}.mid'.format(self.basename)
        self.staff.write('midi', fp=midfile)
        subprocess.run(
            ['timidity',
            '--quiet=2',
            f'-A{self.args.vol}',
            '-T {}'.format(self.song['tempo']),
            midfile])

    def writemusicxml(self):
        f = 'musicxml/{}.musicxml'.format(self.basename)
        self.staff.write('musicxml', fp=f)

    def showpart(self, name):
        fullname = self.tracks[name][0]
        for p in self.staff:
            if p.partName == fullname:
                break
        f = p.flat
        print('{}:'.format(name))
        f.show('text')


def addargs():
    parser = argparse.ArgumentParser(description='arguments ArgumentParser.')
    parser.add_argument('-v', '--vol', default=200, type=int)
    parser.add_argument('-m', '--musicxml', default=False, action='store_true')
    parser.add_argument('filepath', type=str, nargs=1)
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    args = addargs()
    notation = Notation(args)
    with open(args.filepath[0]) as f:
        notation.parser(f.readlines())
    notation.process()
    if args.musicxml:
        notation.writemusicxml()
    else:
        notation.play()
