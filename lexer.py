#!/usr/bin/env python3
import sys
import copy
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
        'LPAREN',
        'RPAREN',
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
        'REST',
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
    t_LPAREN = r'\('
    t_RPAREN = r'\)'
    t_LBRACE = r'\{'
    t_RBRACE = r'\}'
    t_LSQUARE = r'\['
    t_RSQUARE = r'\]'
    t_COLON = r':'

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

    def t_REST(self, t):
        r'[Rr][123468]{1,2}'
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

    def find_column(self, token):
        line_start = self.lexer.lexdata.rfind('\n', 0, token.lexpos) + 1
        return (token.lexpos - line_start) + 1

    def find_line(self, token):
        start = self.lexer.lexdata.rfind('\n', 0, token.lexpos) + 1
        end = self.lexer.lexdata.find('\n', token.lexpos)
        if end == -1:
            return self.lexer.lexdata[start:]
        else:
            return self.lexer.lexdata[start:end]

    # Build the lexer
    def build(self, **kwargs):
        self.lexer = lex.lex(module=self, **kwargs)

    # Test it output
    def process(self, data):
        self.in_parenthesis = 0
        self.in_brace = 0
        self.in_square = 0
        self.in_assign = 0
        self.in_play = 0
        self.last_token = None
        self.lexer.input(data)
        self.result = {
            'info': {},
            'tracks': {},
            'clips': {},
            'playbacks': {}
        }
        self.queue = []
        while True:
            tok = self.lexer.token()
            if not tok:
                break
            self.parser(tok)
            self.last_token = tok
        if not self.states_compare(assign=0, play=0, square=0, parent=0, brace=0):
            self.show_error(self.last_token)

    def show_error(self, token):
        col = self.find_column(token)
        l = self.find_line(token)
        print('Error: at line: {}, pos: {}.'.format(token.lineno, col))
        print(l)
        print(' ' * (col - 1) + '^' * len(token.value))
        sys.exit(1)

    def states_compare(self, assign=0, play=0, square=0, parent=0, brace=0):
        a = [
            self.in_assign,
            self.in_play,
            self.in_square,
            self.in_parenthesis,
            self.in_brace
        ]
        b = [assign, play, square, parent, brace]
        if a == b:
            return True
        else:
            return False

    def states_show(self):
        print("assign: {0}, play: {1}, square: {2}, parenthesis: {3}, brace: {4}.".format(
            self.in_assign, self.in_play, self.in_square, self.in_parenthesis, self.in_brace))

    def parser(self, token):
        # ID COLON [ID | NUMBER | FRACTION | STRING | LPAREN | LSQUARE ]
        if self.states_compare(assign=1, play=0, square=0, parent=0, brace=0):
            allows = ['ID', 'NUMBER', 'STRING',
                      'LPAREN', 'LSQUARE', 'FRACTION']
            if token.type not in allows:
                self.show_error(token)
            if token.type == 'LPAREN':
                self.in_parenthesis = 1
            elif token.type == 'LSQUARE':
                self.in_square = 1
            else:
                _id = self.queue.pop()
                self.result['info'][_id] = token.value
                self.in_assign = 0
        # ID PLAY LSQUARE
        elif self.states_compare(assign=0, play=1, square=0, parent=0, brace=0):
            if token.type == 'LSQUARE':
                self.in_square = 1
            else:
                self.show_error(token)
        # LPAREN [ID | COMMA | STRING | NUMBER ] RPAREN
        elif self.states_compare(assign=1, play=0, square=0, parent=1, brace=0):
            allows = ['ID', 'STRING', 'COMMA', 'NUMBER', 'RPAREN']
            if token.type not in allows:
                self.show_error(token)
            if token.type == 'RPAREN':
                _id = self.queue.pop(0)
                self.result['tracks'][_id] = copy.copy(self.queue)
                self.queue = []
                self.in_parenthesis = 0
                self.in_assign = 0
            else:
                self.queue.append(token.value)
        # LSQUARE [NOTE | REST | BAR | CHORD | TRIP | LBRACE | RBRACE | REF] RSQUARE
        elif self.states_compare(assign=1, play=0, square=1, parent=0, brace=0):
            keywords = ['CHORD', 'TRIP']
            allows = ['NOTE', 'REST', 'RSQUARE', 'REF', 'BAR'] + keywords
            if token.type not in allows:
                self.show_error(token)
            if token.type == 'RSQUARE':
                self.in_square = 0
                self.in_assign = 0
            elif token.type in keywords:
                nx = self.lexer.next()
                if not nx:
                    self.show_error(token)
                if nx.type != 'LBRACE':
                    self.show_error(nx)
                else:
                    self.in_brace = 1
        # LSQUARE [NOTE | REST | BAR | CHORD | TRIP | LBRACE | REF | START | STOP ] RSQUARE
        elif self.states_compare(assign=0, play=1, square=1, parent=0, brace=0):
            keywords = ['CHORD', 'TRIP']
            allows = ['NOTE', 'REST', 'RSQUARE', 'REF',
                      'BAR', 'START', 'STOP'] + keywords
            if token.type not in allows:
                self.show_error(token)
            if token.type == 'RSQUARE':
                self.in_square = 0
                self.in_play = 0
            elif token.type in keywords:
                nx = self.lexer.next()
                if not nx:
                    self.show_error(token)
                if nx.type != 'LBRACE':
                    self.show_error(nx)
                else:
                    self.in_brace = 1
            pass
        # LBRACE [NOTE] RBRACE
        elif self.in_brace > 0:
            if token.type not in ['NOTE', 'RBRACE']:
                self.show_error(token)
            if token.type == 'RBRACE':
                self.in_brace = 0
        # (SEGMENT) | (ID [ COLON | PLAY ])
        elif self.states_compare(assign=0, play=0, square=0, parent=0, brace=0):
            if token.type not in ['ID', 'SEGMENT']:
                self.show_error(token)
            if token.type == 'ID':
                nx = self.lexer.next()
                if not nx:
                    self.show_error(token)
                elif nx.type == 'COLON':
                    self.in_assign = 1
                elif nx.type == 'PLAY':
                    self.in_play = 1
                else:
                    self.show_error(nx)
                self.queue.append(token.value)
        else:
            print("[Warning]: Unknown states!")
            self.states_show()


if __name__ == '__main__':
    m = MyLexer()
    m.build(debug=False)
    with open(sys.argv[1]) as f:
        m.process(f.read())
    print(m.result)
