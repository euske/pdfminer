import re
import ply.lex as lex

states = (
    ('instring', 'exclusive'),
)

tokens = (
    'COMMENT', 'HEXSTRING', 'INT', 'FLOAT', 'LITERAL', 'KEYWORD', 'STRING', 'OPERATOR'
)

delimiter = r'\(\)\<\>\[\]\{\}\/\%\s'
delimiter_end = r'(?=[%s]|$)' % delimiter

def t_COMMENT(t):
    # r'^%!.+\n'
    r'%.*\n'
    pass

RE_SPC = re.compile(r'\s')
RE_HEX_PAIR = re.compile(r'[0-9a-fA-F]{2}|.')
@lex.TOKEN(r'<[0-9A-Fa-f\s]*>' + delimiter_end)
def t_HEXSTRING(t):
    cleaned = RE_SPC.sub('', t.value[1:-1])
    pairs = RE_HEX_PAIR.findall(cleaned)
    token_bytes = bytes([int(pair, 16) for pair in pairs])
    try:
        t.value = token_bytes.decode('ascii')
    except UnicodeDecodeError:
        # should be kept as bytes
        t.value = token_bytes
    return t

@lex.TOKEN(r'(\-|\+)?[0-9]+' + delimiter_end)
def t_INT(t):
    t.value = int(t.value)
    return t

@lex.TOKEN(r'(\-|\+)?([0-9]+\.|[0-9]*\.[0-9]+|[0-9]+\.[0-9]*)((e|E)[0-9]+)?' + delimiter_end)
def t_FLOAT(t):
    t.value = float(t.value)
    return t

RE_LITERAL_HEX = re.compile(r'#[0-9A-Fa-f]+')
@lex.TOKEN(r'/.+?' + delimiter_end)
def t_LITERAL(t):
    newvalue = t.value[1:]
    # If there's '#' chars in the literal, we much de-hex it
    def re_sub(m):
        # convert any hex str to int (without the # char) and the convert that 
        return bytes.fromhex(m.group(0)[1:]).decode('latin-1')
    newvalue = RE_LITERAL_HEX.sub(re_sub , newvalue)
    # If there's any lone # char left, remove them
    newvalue = newvalue.replace('#', '')
    t.value = newvalue
    return t

def t_OPERATOR(t):
    r'{|}|<<|>>|\[|\]'
    return t

t_KEYWORD = r'.+?' + delimiter_end

def t_instring(t):
    r'\('
    t.lexer.value_buffer = []
    t.lexer.string_startpos = t.lexpos
    t.lexer.level = 1
    t.lexer.begin('instring')

def t_instring_lparen(t):     
    r'\('
    t.lexer.level +=1
    t.lexer.value_buffer.append('(')

def t_instring_rparen(t):
    r'\)'
    t.lexer.level -=1

    if t.lexer.level == 0:
         t.value = ''.join(t.lexer.value_buffer)
         if any(ord(c) > 0x7f for c in t.value):
             t.value = t.value.encode('latin-1')
         t.type = "STRING"
         t.lexpos = t.lexer.string_startpos
         t.lexer.begin('INITIAL')           
         return t
    else:
        t.lexer.value_buffer.append(')')

RE_STRING_ESCAPE = re.compile(r'\\[btnfr()\\]')
RE_STRING_OCTAL = re.compile(r'\\[0-7]{1,3}')
RE_STRING_LINE_CONT = re.compile(r'\\\n')
ESC_STRING = { 'b': '\b', 't': '\t', 'n': '\n', 'f': '\f', 'r': '\r', '(': '(', ')': ')', '\\': '\\' }
def t_instring_contents(t):
    r'[^()]+'
    s = t.value
    repl = lambda m: ESC_STRING[m.group(0)[1]]
    s = RE_STRING_ESCAPE.sub(repl, s)
    repl = lambda m: chr(int(m.group(0)[1:], 8))
    s = RE_STRING_OCTAL.sub(repl, s)
    s = RE_STRING_LINE_CONT.sub('', s)
    t.lexer.value_buffer.append(s)

t_instring_ignore = ''
t_ignore = ' \t\r\n'

# Error handling rule
def t_error(t):
    print("Illegal character '%s'" % t.value[0])
    t.lexer.skip(1)
t_instring_error = t_error

lexer = lex.lex()

def main():
    TESTDATA = r'''%!PS
begin end
 "  @ #
/a/BCD /Some_Name /foo#5f#xbaa
0 +1 -2 .5 1.234
(abc) () (abc ( def ) ghi)
(def\040\0\0404ghi) (bach\\slask) (foo\nbaa)
(this % is not a comment.)
(foo
baa)
(foo\
baa)
<> <20> < 40 4020 >
<abcd00
12345>
func/a/b{(c)do*}def
[ 1 (z) ! ]
<< /foo (bar) >>
'''
    lexer.input(TESTDATA)
    while True:
        tok = lexer.token()
        if not tok:
            break
        print(repr(tok))

if __name__ == '__main__':
    main()