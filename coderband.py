#!/usr/bin/env python3
import sys
import os
import argparse


def cbdparser(fp):
    from parser import MyLexer
    m = MyLexer()
    m.build(debug=False)
    with open(fp) as f:
        m.process(f.read())
    return m.result

def cbd2music21(cbd):
    pass

def play(args):
    if args.file:
        fp = args.file[0]
        # check file type by suffix
        _, suffix = os.path.splitext(fp)
        if suffix == '.cbd':
            res = cbdparser(fp)
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
    args.func(args)

if __name__ == '__main__':
    getopts()
