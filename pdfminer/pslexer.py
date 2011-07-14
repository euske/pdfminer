import re
import ply.lex as lex

states = (
    ('instring', 'exclusive'),
)

tokens = (
    'COMMENT', 'HEXSTRING', 'INT', 'FLOAT', 'LITERAL', 'KEYWORD', 'STRING', 'OPERATOR'
)

delimiter = r'\(\)\<\>\[\]\{\}\/\%\s'
delimiter_end = r'(?=[%s])' % delimiter

def t_COMMENT(t):
    r'^%!.+\n'
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

t_INT = r'(\-|\+)?[0-9]+' + delimiter_end
t_FLOAT = r'(\-|\+)?([0-9]+\.|[0-9]*\.[0-9]+|[0-9]+\.[0-9]*)((e|E)[0-9]+)?' + delimiter_end

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
         t.type = "STRING"
         t.lexer.begin('INITIAL')           
         return t
    else:
        t.lexer.value_buffer.append(')')

def t_instring_octal(t):
    r'\\[0-7]{1,3}'
    # for some reason, there can be octal-encoded strings in there.
    t.lexer.value_buffer.append(chr(int(t.value[1:], 8)))

def t_instring_line_continuation(t):
    r'\\\n'
    # When we have a '\' char at the end of a line in a string, we ignore it.
    pass

def t_instring_therest(t):
    r'[^()]'
    # we don't care about this, we get the contents of the string when we hit the closing paren
    t.lexer.value_buffer.append(t.value)

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