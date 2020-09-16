#!/usr/bin/env python3
import sys
import copy
import pprint
import re
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
        r'[\+\-]{0,1}[0-9]*[/]{0,1}[0-9]+'
        if t.value.find('/') > -1:
            t.type = 'FRACTION'
        return t

    def t_NOTE(self, t):
        r'([cdefgab][\']{0,2}[#-]{0,4}[123468]{1,2}[.]{0,4}[~]{0,1}|[CDEFGAB]{1,3}[#-]{0,1}[123468]{1,2}[.]{0,4}[~]{0,1})'
        return t

    def t_REST(self, t):
        r'[Rr][123468]{1,2}[.]{0,4}'
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
        self.pp = pprint.PrettyPrinter(indent=2)
        self.result = {
            'info': {},
            'tracks': {},
            'clips': {},
            'playbacks': {}
        }
        self.queue = []
        self.timesign_table = {
            '4/4': 32,
            '3/4': 24,
            '6/8': 24,
            '2/4': 16,
            '3/8': 12
        }
        self.time_signature = '4/4'
        self.playback = 0
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

    def error_msg(self, token, msg):
        col = self.find_column(token)
        l = self.find_line(token)
        print('[Error@line: {}, pos: {}] {}'.format(token.lineno, col, msg))
        print(l)
        print(' ' * (col - 1) + '^' * len(token.value))
        sys.exit(1)

    def states_compare(self, assign=0, play=0, square=0, parent=0, brace=0):
        a = [
            self.in_assign,
            self.in_play,
            self.in_square,
            self.in_parenthesis,
            self.in_brace,
        ]
        b = [assign, play, square, parent, brace]
        if a == b:
            return True
        else:
            return False

    def states_show(self):
        print("assign: {0}, play: {1}, square: {2}, parenthesis: {3}, brace: {4}.".format(
            self.in_assign, self.in_play, self.in_square, self.in_parenthesis, self.in_brace))

    def result_show(self):
        self.pp.pprint(self.result)

    # notation methods
    def note_len(self, note):
        num = int(re.findall(r'\d+', note)[0])
        if num not in [1, 2, 4, 8, 16, 32]:
            return -1
        n1 = 32 / num
        curr = n1
        dots = note.count('.')
        for _ in range(dots):
            n1 += curr / 2
            curr = curr / 2
        return n1

    def notation_check(self, note, token):
        if token.type in ['NOTE', 'REST']:
            nl = self.note_len(note)
            if nl < 0:
                self.error_msg(token, "Note length is invalid!")
            if self.in_brace > 0:
                if len(self._notes) > 1:
                    n = self._notes[-1]
                    a = re.sub('[a-gA-G\-\'\#]', '', n)
                    b = re.sub('[a-gA-G\-\'\#]', '', token.value)
                    if a != b:
                        self.error_msg(token, "chord/trip must keep the same note length!")
        elif token.type in ['REF']:
            pass

    def track_measure(self, track):
        pos = 0
        for n in track:
            if type(n) is list:
                n = n[-1]
            pos += self.note_len(n)
        return pos

    def fill_rest(self, measure):
        rests = []
        m = measure
        for i in [32, 16, 8, 4, 2, 1]:
            q = int(m // i)
            r = int(m % i)
            if q > 0:
                rests += ['r1'] * q
            if r == 0:
                break
            m = r
        return rests

    def notation_segment(self, token):
        playbacks = self.result['playbacks']
        tracks = self.result['tracks']
        if not playbacks:
            return
        m = {}
        max_ = 0
        for k in tracks.keys():
            if k not in playbacks:
                playbacks[k] = []
                m[k] = 0
            else:
                pos = self.track_measure(playbacks[k])
                m[k] = pos
                if max_ < pos:
                    max_ = pos
        for k, v in m.items():
            if v < max_:
                rests = self.fill_rest(max_ - v)
                playbacks[k].extend(rests)

    def parser(self, token):
        # ID COLON [ID | NUMBER | FRACTION | STRING | LPAREN | LSQUARE ]
        if self.states_compare(assign=1):
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
                if token.type == 'STRING':
                    self.result['info'][_id] = token.value.replace('"', '')
                else:
                    self.result['info'][_id] = token.value
                self.in_assign = 0
        # ID PLAY LSQUARE
        elif self.states_compare(play=1):
            if token.type == 'LSQUARE':
                self.in_square = 1
            else:
                self.show_error(token)
        # LPAREN [ID | COMMA | STRING | NUMBER ] RPAREN
        elif self.states_compare(assign=1, parent=1):
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
        elif self.states_compare(assign=1, square=1):
            keywords = ['CHORD', 'TRIP']
            allows = ['NOTE', 'REST', 'RSQUARE', 'BAR'] + keywords
            if token.type not in allows:
                self.show_error(token)
            if token.type == 'RSQUARE':
                _id = self.queue.pop(0)
                self.result['clips'][_id] = copy.copy(self.queue)
                self.queue = []
                self.in_square = 0
                self.in_assign = 0
            elif token.type in keywords:
                nx = self.lexer.next()
                if not nx:
                    self.show_error(token)
                if nx.type != 'LBRACE':
                    self.show_error(nx)
                else:
                    self._notes = [token.value]
                    self.in_brace = 1
            elif token.type in ['NOTE', 'REST']:
                self.notation_check(token.value, token)
                self.queue.append(token.value)
            elif token.type in ['BAR']:
                pass

        # LSQUARE [NOTE | REST | BAR | CHORD | TRIP | LBRACE | REF | START | STOP ] RSQUARE
        elif self.states_compare(play=1, square=1):
            keywords = ['CHORD', 'TRIP']
            allows = ['NOTE', 'REST', 'RSQUARE', 'REF',
                      'BAR'] + keywords
            if token.type not in allows:
                self.show_error(token)
            if token.type == 'RSQUARE':
                if self.playback > 0:
                    _id = self.queue.pop(0)
                    if _id in self.result['playbacks']:
                        p = self.result['playbacks'][_id]
                        p = p.extend(self.queue)
                    else:
                        self.result['playbacks'][_id] = list(self.queue)
                self.queue = []
                self.in_square = 0
                self.in_play = 0
            elif token.type in keywords:
                nx = self.lexer.next()
                if not nx:
                    self.show_error(token)
                if nx.type != 'LBRACE':
                    self.show_error(nx)
                else:
                    self._notes = [token.value]
                    self.in_brace = 1
            elif token.type in ['NOTE', 'REST']:
                self.notation_check(token.value, token)
                self.queue.append(token.value)
            elif token.type in ['REF']:
                clips = self.result['clips']
                clip = token.value.replace('$', '')
                if clip not in clips:
                    self.show_error(token)
                else:
                    self.notation_check(clips[clip], token)
                    self.queue.extend(clips[clip])
            elif token.type in ['BAR']:
                pass
        # LBRACE [NOTE] RBRACE
        elif self.in_brace > 0:
            if token.type not in ['NOTE', 'RBRACE']:
                self.show_error(token)
            if token.type == 'RBRACE':
                if len(self._notes) == 1:
                    self.error_msg(token, "chord/trip is empty!")
                self.queue.append(copy.copy(self._notes))
                self._notes = []
                self.in_brace = 0
            else:
                self.notation_check(token.value, token)
                self._notes.append(token.value)
        # (SEGMENT) | (ID [ COLON | PLAY ])
        elif self.states_compare():
            if token.type not in ['ID', 'SEGMENT', 'START', 'STOP']:
                self.show_error(token)
            if token.type == 'ID':
                nx = self.lexer.next()
                if not nx:
                    self.show_error(token)
                elif nx.type == 'COLON':
                    self.in_assign = 1
                elif nx.type == 'PLAY':
                    self.in_play = 1
                    # check the track exists
                    if token.value not in self.result['tracks']:
                        self.show_error(token)
                else:
                    self.show_error(nx)
                self.queue.append(token.value)
            elif token.type == 'SEGMENT':
                self.notation_segment(token)
            elif token.type in ['START']:
                self.playback = 1
            elif token.type in ['STOP']:
                self.playback = 0
                self.notation_segment(token)
        else:
            print("[Warning]: Unknown states!")
            self.states_show()


if __name__ == '__main__':
    m = MyLexer()
    m.build(debug=False)
    with open(sys.argv[1]) as f:
        m.process(f.read())
    m.result_show()
