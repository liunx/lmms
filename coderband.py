#!/usr/bin/env python3
import sys
import os
import argparse
import subprocess
from mcore import MCore
from parser import MyLexer

root = os.path.dirname(sys.argv[0])

def cbdparser(fp):
    m = MyLexer()
    m.build(debug=False)
    with open(fp) as f:
        m.process(f.read())
    return m.result

def playmidi(fp, vol, tempo):
    subprocess.run(
        ['timidity',
        '--quiet=2',
        f'-A{vol}',
        f'-T {tempo}',
        fp])

def play(args):
    if args.file:
        fp = args.file[0]
        if not os.path.exists(fp):
            print('Error: {} not exist!'.format(fp))
        # check file type by suffix
        _, suffix = os.path.splitext(fp)
        if suffix == '.cbd':
            tempo = args.tempo
            res = cbdparser(fp)
            try:
                tempo = int(res['info']['tempo'])
            except:
                print("Warning: tempo not found!")
            mc = MCore()
            mc.cbd(res)
            mid = os.path.basename(fp).replace('.cbd', '.mid')
            midfp = '{}/midi/{}'.format(root,mid)
            mc.writemidi(midfp)
            playmidi(midfp, args.vol, tempo)
        else:
            print("Don't support this file type!")
            sys.exit(1)

def convert(args):
    ifp = args.input[0]
    ofp = args.output
    _, input_suffix = os.path.splitext(ifp)
    mc = MCore()
    if input_suffix == '.cbd':
        res = cbdparser(ifp)
        mc.cbd(res)
    elif input_suffix in ['.xml', '.musicxml']:
        mc.xml(ifp)
    elif input_suffix in ['.mid', '.midi']:
        mc.midi(ifp)
    else:
        print("Error: Unsupported input file type!")
        sys.exit(1)
    _, output_suffix = os.path.splitext(ofp)
    if output_suffix == '.cbd':
        mc.writecbd(ofp, step=4)
    elif output_suffix in ['.xml', '.musicxml']:
        mc.writexml(ofp)
    elif output_suffix in ['midi', 'mid']:
        mc.writemidi(ofp)
    elif output_suffix == '.mmp':
        if input_suffix not in ['.cbd']:
            print("Error: Ony support input file type of *.cbd!")
            sys.exit(1)
        mc.writelmms(ofp)
    else:
        print("Error: Unsupported output file type!")
        sys.exit(1)

def sing(args):
    print(args)

def getopts():
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--version', type=str)
    parser.add_argument('-d', '--debug', default=False, action='store_true')
    subparsers = parser.add_subparsers(title="Available Commands")
    # play
    sub = subparsers.add_parser('play', help="play *.cbd, *.mid, *.xml file")
    sub.add_argument('-v', '--vol', default=200, type=int)
    sub.add_argument('-t', '--tempo', default=120, type=int)
    sub.add_argument('file', type=str, nargs=1)
    sub.set_defaults(func=play)
    # sing
    sub = subparsers.add_parser('sing', help="sing  notation")
    sub.set_defaults(func=sing)
    # write
    sub = subparsers.add_parser('conv', help="convert from {*.cbd, *.xml, *mid} to {*.cbd, *.mid, *.xml, *.mmp} file")
    sub.add_argument('input', type=str, nargs=1)
    sub.add_argument('-o', '--output', type=str, required=True)
    sub.set_defaults(func=convert)
    # parset args
    args = parser.parse_args()
    try:
        func = args.func
    except AttributeError:
        parser.print_help()
        sys.exit(1)
    func(args)

if __name__ == '__main__':
    getopts()
