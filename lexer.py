#!/usr/bin/env python3
import sys
import ply.lex as lex


class MyLexer(object):
    # List of token names.   This is always required
    tokens = [
        'NOTE',
        'ASSIGN',
        'ID',
        'NUMBER',
        'STRING',
        'COLON',
        'COMMA',
        'DIV',
        'LBRACE',
        'RBRACE',
        'LSQUARE',
        'RSQUARE',
        'FRACTION',
        'PLAY',
        'SEGMENT',
        'BAR',
        'START',
        'STOP',
        'REF',
    ]

    reserved = {
        'chord': 'CHORD',
        'trip': 'TRIP',
    }

    tokens = tokens + list(reserved.values())
    literals = []
    # Regular expression rules for simple tokens
    t_PLAY = r'->'
    t_SEGMENT = r'--'
    t_BAR = r'\|'
    t_START = r'>>'
    t_STOP = r'<<'

    def t_LBRACE(self, t):
        r'\{'
        return t

    def t_RBRACE(self, t):
        r'\}'
        return t

    def t_LSQUARE(self, t):
        r'\['
        return t

    def t_RSQUARE(self, t):
        r'\]'
        return t

    # A regular expression rule with some action code
    # Note addition of self parameter since we're in a class
    def t_REF(self, t):
        r'\$[a-zA-Z_][a-zA-Z_0-9]*'
        return t

    def t_NUMBER(self, t):
        r'[0-9]*[/]{0,1}[0-9]+'
        if t.value.find('/') > -1:
            t.type = 'FRACTION'
        return t

    def t_NOTE(self, t):
        r'([cdefgab][\']{0,2}[#-]{0,1}[123468]{1,2}[.]{0,3}|[CDEFGAB]{1,3}[#-]{0,1}[123468]{1,2}[.]{0,3})'
        return t

    def t_ASSIGN(self, t):
        r'[a-zA-Z_][a-zA-Z_0-9]*[ ]*:'
        return t

    def t_ID(self, t):
        r'[a-zA-Z_][a-zA-Z_0-9]*'
        t.type = self.reserved.get(t.value, 'ID')
        return t

    def t_STRING(self, t):
        r'\"([^\\\n]|(\\.))*?\"'
        return t

    # Define a rule so we can track line numbers
    def t_newline(self, t):
        r'\n+'
        t.lexer.lineno += len(t.value)

    # A string containing ignored characters (spaces and tabs)
    t_ignore = ' \t'
    t_ignore_COMMA = r','
    t_ignore_COMMENT = r'\@.*'

    # Error handling rule
    def t_error(self, t):
        print("Illegal character '%s'" % t.value[0])
        t.lexer.skip(1)

    # Build the lexer
    def build(self, **kwargs):
        self.lexer = lex.lex(module=self, **kwargs)

    # Test it output
    def test(self, data):
        self.lexer.input(data)
        while True:
            tok = self.lexer.token()
            if not tok:
                break
            print(tok)


if __name__ == '__main__':
    m = MyLexer()
    m.build()
    with open(sys.argv[1]) as f:
        m.test(f.read())
