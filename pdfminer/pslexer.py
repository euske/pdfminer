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
@lex.TOKEN(r'<[0-9A-Fa-f\s]*>')
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

RE_LITERAL_HEX = re.compile(r'#[0-9A-Fa-f]{2}')
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

# The parens situation: it's complicated. We can have both escaped parens and unescaped parens.
# If they're escaped, there's nothing special, we unescape them and add them to the string. If
# they're not escaped, we have to count how many of them there are, to know when a rparen is the
# end of the string. The regular expression for this is messed up, so what we do is when we hit
# a paren, we look if the previous buffer ended up with a backslash. If it did, we don't to paren
# balancing.

def t_instring_lparen(t):     
    r'\('
    is_escaped = t.lexer.value_buffer and t.lexer.value_buffer[-1].endswith('\\')
    if is_escaped:
        t.lexer.value_buffer[-1] = t.lexer.value_buffer[-1][:-1]
    else:
        t.lexer.level +=1
    t.lexer.value_buffer.append('(')

def t_instring_rparen(t):
    r'\)'
    is_escaped = t.lexer.value_buffer and t.lexer.value_buffer[-1].endswith('\\')
    if is_escaped:
        t.lexer.value_buffer[-1] = t.lexer.value_buffer[-1][:-1]
    else:
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

RE_STRING_ESCAPE = re.compile(r'\\[btnfr\\]')
RE_STRING_OCTAL = re.compile(r'\\[0-7]{1,3}')
RE_STRING_LINE_CONT = re.compile(r'\\\n|\\\r|\\\r\n')
ESC_STRING = { 'b': '\b', 't': '\t', 'n': '\n', 'f': '\f', 'r': '\r', '\\': '\\' }

def repl_string_escape(m):
    return ESC_STRING[m.group(0)[1]]

def repl_string_octal(m):
    i = int(m.group(0)[1:], 8)
    if i < 0xff: # we never want to go above 256 because it's unencodable
        return chr(i)
    else:
        return m.group(0)

def t_instring_contents(t):
    r'[^()]+'
    s = t.value
    s = RE_STRING_ESCAPE.sub(repl_string_escape, s)
    s = RE_STRING_OCTAL.sub(repl_string_octal, s)
    s = RE_STRING_LINE_CONT.sub('', s)
    t.lexer.value_buffer.append(s)

t_instring_ignore = ''
t_ignore = ' \t\r\n'

# Error handling rule
def t_error(t):
    print("Illegal character '%r'" % t.value[0])
    t.lexer.skip(1)
t_instring_error = t_error

lexer = lex.lex()