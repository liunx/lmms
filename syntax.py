#!/usr/bin/env python3
import os
import sys
import ply.lex as lex
import ply.yacc as yacc


class Base:
    """
    Base class for a lexer/parser that has the rules defined as methods
    """
    tokens = ()
    precedence = ()
    meta_info = {}
    params = {}
    queue = []
    lineno = 1
    timesign = '4/4'

    def __init__(self, **kw):
        self.debug = kw.get('debug', 0)
        try:
            modname = os.path.split(os.path.splitext(__file__)[0])[
                1] + "_" + self.__class__.__name__
        except:
            modname = "parser" + "_" + self.__class__.__name__
        self.debugfile = modname + ".dbg"
        # print self.debugfile

        # Build the lexer and parser
        lex.lex(module=self, debug=self.debug)
        yacc.yacc(module=self,
                  debug=self.debug,
                  debugfile=self.debugfile)

    def check_bar(self, bar):
        return True

    def check_nested(self, notes):
        for n in notes:
            if type(n) is dict:
                return False
        return True

    def check_chord(self, notes):
        return True

    def check_trip(self, notes):
        return True

    def run(self, lines):
        yacc.parse(lines)
        return
        for l in lines:
            yacc.parse(l)
            self.lineno += 1


class Parser(Base):

    tokens = (
        'NOTE', 'REST',
        'STRING',
        'COMMA', 'COLON', 'BAR',
        'ID', 'NUMBER', 'FRACTION',
        'CLIP',
        'LSQUARE', 'RSQUARE',
        'LBRACE', 'RBRACE',
        'EQUAL',
        'PLAY', 'BEGIN', 'END',
    )

    # Tokens

    t_NOTE = r'([cdefgab][\']{0,2}[#-]{0,1}[123468]{1,2}[.]{0,3}|[CDEFGAB]{1,3}[#-]{0,1}[123468]{1,2}[.]{0,3})'
    t_COMMA = r','
    t_COLON = r':'
    t_EQUAL = r'='
    t_PLAY = r'->'
    t_BEGIN = r'>>'
    t_END = r'<<'
    t_LSQUARE = r'\['
    t_RSQUARE = r'\]'
    t_ID = r'[a-zA-Z_][a-zA-Z0-9_]*'

    # String literal
    t_STRING = r'\"([^\\\n]|(\\.))*?\"'

    t_CLIP = r'\$[a-zA-Z_][a-zA-Z0-9_]*'

    def t_FRACTION(self, t):
        r'[1-9]/[1-9]'
        return t

    def t_REST(self, t):
        r'[Rr][123468]{1,2}'
        return t

    def t_NUMBER(self, t):
        r'\d+'
        try:
            t.value = int(t.value)
        except ValueError:
            print("Integer value too large %s" % t.value)
            t.value = 0
        # print "parsed number %s" % repr(t.value)
        return t

    def t_COMMENT(self, t):
        r'\#.*'

    def t_BAR(self, t):
        r'\|'
        return t

    def t_LBRACE(self, t):
        r'\{'
        return t

    def t_RBRACE(self, t):
        r'\}'
        return t

    t_ignore = " \t"

    def t_newline(self, t):
        r'\n+'
        t.lexer.lineno += t.value.count("\n")
        t.lexer.skip(1)

    def t_error(self, t):
        print("Illegal character '{}' @line: {}".format(t.value[0], t.lexer.lineno))
        sys.exit(1)

    # Parsing rules

    def p_statement_declare(self, p):
        'statement : ID COLON expression'
        if not self.queue:
            print("ERROR: {}'s value is None!".format(p[1]))
            sys.exit(1)
        self.meta_info[p[1]] = self.queue[0]
        self.queue = []

    def p_statement_params(self, p):
        'statement : ID EQUAL expression'
        if not self.queue:
            print("ERROR: {}'s value is None!".format(p[1]))
            sys.exit(1)
        self.params[p[1]] = self.queue
        self.queue = []

    def p_statement_notation(self, p):
        'statement : ID PLAY LSQUARE notation RSQUARE'
        if type(p[4]) is str:
            p[4] = [p[4]]
        self.queue.insert(0, p[4])
        print(p[1], self.queue)
        self.queue = []

    def p_params_expand(self, p):
        'expression : expression COMMA expression'

    def p_expression_string(self, p):
        'expression : STRING'
        self.queue.append(p[1])

    def p_expression_id(self, p):
        'expression : ID'
        self.queue.append(p[1])

    def p_expression_number(self, p):
        'expression : NUMBER'
        self.queue.append(p[1])

    def p_expression_fraction(self, p):
        'expression : FRACTION'
        self.queue.append(p[1])

    def p_notation_expand(self, p):
        'notation : notation notation'
        if type(p[2]) is list:
            p[0] = [p[1]] + p[2]
        else:
            p[0] = [p[1], p[2]]

    def p_notation_bar(self, p):
        'notation : notation BAR notation'
        bar = p[3]
        if not self.check_bar(bar):
            self.p_error(p)
        if type(bar) is str:
            bar = [bar]
        self.queue.insert(0, bar)
        p[0] = p[1]

    def p_notation_mixer(self, p):
        'notation : ID LBRACE mixers RBRACE'
        ret = True
        if p[1] == 'chord':
            ret = self.check_chord(p[3])
        elif p[1] == 'trip':
            ret = self.check_trip(p[3])
        if not ret:
            self.p_error(p)
        p[0] = {p[1]: p[3]}

    def p_mixers_expand(self, p):
        'mixers : mixers mixers'
        p[0] = [p[1], p[2]]

    def p_mixers_note(self, p):
        'mixers : NOTE'
        p[0] = p[1]

    def p_notation_note(self, p):
        'notation : NOTE'
        p[0] = p[1]

    def p_notation_rest(self, p):
        'notation : REST'
        p[0] = p[1]

    def p_notation_clip(self, p):
        'notation : CLIP'

    def p_notation_begin(self, p):
        'notation : BEGIN'

    def p_notation_end(self, p):
        'notation : END'

    def p_error(self, p):
        if p:
            print("Syntax error at '{}', line: {}, pos: {}".format(p.value, p.lineno, p.lexpos))
            sys.exit(1)
        else:
            pass


if __name__ == '__main__':
    parser = Parser()
    with open(sys.argv[1]) as f:
        parser.run(f.read())
    print(parser.meta_info)
    print(parser.params)
