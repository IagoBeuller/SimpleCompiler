from rply import LexerGenerator, Token
from prettytable import PrettyTable
from rply.errors import LexingError

class Lexer:
    token_types = {
            # Reserved Keywords
            'FLOATTYPE' : r'float',
            'INTTYPE'   : r'int',
            'STRINGTYPE': r'str',
            'FLOAT'     : r'float|(\d*\.\d+)',
            'INT'       : r'\d+',
            'STRING'    : r'"(.*(?<!\\))"|\'(.*(?<!\\))\'',
            # 'STRINGERROR': r'"(.*(?<!\\)\n*.*\n)|\'(.*(?<!\\))',
            'TUPLE'     : r'tuple',#|\((.*(?<!\\))\)',
            'LIST'      : r'list',#|\[(.*(?<!\\))\]',
            'DICT'      : r'dict',#|\[(.*(?<!\\))\]',
            'VARIABLE'  : r'var',
            'IFSTATE'   : r'if',
            'ELSESTATE' : r'else',
            'ELIFSTATE' : r'elif',
            'FUNCTION'  : r'def',
            'CLASS'     : r'class',
            'FLOOP'     : r'for',
            'WLOOP'     : r'while',
            #'DLOOP'    : 'do',
            'SWITCH'    : r'switch',
            'PASS'      : r'pass',
            'BREAK'     : r'break',
            'CONTINUE'  : r'continue',
            'PRINT'     : r'print',

            # Symbols and Operators
            'INC'       : r'\+=|\+\+',
            'DEC'       : r'-=|--',
            'PLUS'      : r'\+',
            'MINUS'     : r'-',
            'MUL'       : r'\*',
            'DIV'       : r'/',
            'LPAR'      : r'\(',
            'RPAR'      : r'\)',
            'LBKT'      : r'\[',
            'RBKT'      : r'\]',
            'LBRC'      : r'\{',
            'RBRC'      : r'\}',
            'EQUAL'     : r'==',
            'GEQUAL'    : r'>=',
            'LEQUAL'    : r'<=',
            'IS'        : r'=',
            #'IS'         : 'is',
            'NOT'       : r'!',
            # 'NOT'       : 'not',
            'GREATER'   : r'>',
            'LOWER'     : r'<',
            'ACCESS'    : r'\.',
            'SEPARATE'  : r',',
            'SCOPE'     : r':',
            'ABSTRACT'  : r';',
            'LINEBREAK' : '\n',
            'TAB'       : '\t',

            # User Definition
            'NAME'      : r'[a-zA-z][a-zA-Z0-9_]*',
        }
    def __init__(self):
        self.generator = LexerGenerator()

    def tokenize(self, code):
        self.generator.ignore(r'\s+')            # Ignore White Spaces
        self.generator.ignore(r'!#[\s\S]*?#!')   # Ignore Multiline Comments
        self.generator.ignore(r'#(.*?)*(\n|$)')  # Ignore Single Line Comments

        for type in self.token_types:
            self.generator.add(type, self.token_types[type])

        l = self.generator.build()
        try:
            self.tokens = list(l.lex(code))
            error = None
        except LexingError as e:
            self.tokens = []
            error_pos = e.source_pos
            line_error = code.splitlines()[error_pos.lineno-1]
            error = f"LexerError: Unexpected keyword at line {error_pos.lineno}, column {error_pos.colno}: \n{line_error}\n" + \
                " " * (len(line_error[:error_pos.colno]) - 1) + "^"

        return self.tokens, error

    def tabulated_tokens(self):
        table = PrettyTable(["Linha", "Token", "Tipo", "Reservada"])
        print(dir(self.tokens[0].source_pos))
        for token in self.tokens:
            # is_reserved = token.name != "NAME" and token.name.isalpha()  # Includes symbols too
            is_reserved = token.name != "NAME" and token.value.isalpha()  # Exclude Symbols
            table.add_row([token.source_pos.lineno, token.value, token.name, is_reserved])
        return table

    def showResult(self):
        print("Tokens:")
        print(self.tabulated_tokens())