#!/usr/bin/env python3
import sys
from parser import MyLexer

if __name__ == '__main__':
    m = MyLexer()
    m.build(debug=False)
    with open(sys.argv[1]) as f:
        m.process(f.read())
    m.result_show()