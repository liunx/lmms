#!/usr/bin/env python3
import sys
import os
import argparse
import subprocess
from mcore import MCore

root = os.path.dirname(sys.argv[0])

def cbdparser(fp):
    from parser import MyLexer
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
            mc = MCore(res)
            mid = os.path.basename(fp).replace('.cbd', '.mid')
            midfp = '{}/midi/{}'.format(root,mid)
            mc.writemidi(midfp)
            playmidi(midfp, args.vol, tempo)
        else:
            print("Don't support this file type!")
            sys.exit(1)

def write(args):
    print(args)

def sing(args):
    print(args)

def getopts():
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--version', type=str)
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
    sub = subparsers.add_parser('write', help="write to *.cbd, *.mid, *.xml file")
    sub.set_defaults(func=write)
    # parset args
    args = parser.parse_args()
    try:
        args.func(args)
    except AttributeError:
        parser.print_help()

if __name__ == '__main__':
    getopts()
