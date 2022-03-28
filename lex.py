import sys
from enum import Enum, auto
class TokenType(Enum):
    Id = auto() # Identifiers, It would be a string starts with lowercase letter, followed by lower or upper letter.
    Tuple = auto() # Tuple. It would A-Z.
    Integer = auto()
    String = auto()
    LeftBrace = auto() # {
    RightBrace = auto() # }
    LeftParentheses = auto() # (
    RightParentheses = auto() # )
    Greater = auto() # >
    Less = auto() # <
    Equal = auto() # =
    Geq = auto() # >=
    Leq = auto() # <=
    Exist = auto() # ∃
    Every = auto() # ∀
    Imply = auto() # ->
    Dot = auto() # .
    Belong = auto() # ∈
    And = auto() # ∧
    Or = auto() # ∨
    Neg = auto() # ¬
    Pipe = auto() # |

class Token():
    def __init__(self, tokenType, value = None):
        self.type = tokenType
        self.value = value

    def __str__ (self):
        if self.value is None:
            return 'Token(type=' + str(self.type) + ')'
        else:
            return 'Token(type=' + str(self.type) + ', value="' + self.value+ '")'

    def getType(self):
        return self.type

    def getValue(self):
        return self.value

    def __cmp__(self, other):
        return (self.type == other.type) and (self.value == other.value)

# getTokens function would take a source program as input, and return an array of token.
# Each token would be a dict: {'type': Token, 'value': actual value of the token}
def getTokens(source):
    lines = source.splitlines()
    tokenList = []
    for i in range(len(lines)):
        tokenList.extend(getTokensForLine(lines[i],i+1))
    return tokenList

# getTokensFor line would take a line without comment as input and output a list of tokens after tokenization.
def getTokensForLine(line, linenumber):
    tokens = []
    while len(line) > 0:
        #print(len(line))
        cur = str(line[0])
        #print(cur)
        if cur == ' ' or cur == '\t':
            # ignore the space and the \t
            line = line[1:]
        elif cur.islower():
            newToken, line = tokenizeId(line)
            tokens.append(newToken)
        elif cur.isupper():
            newToken, line = tokenizeTuple(line)
            tokens.append(newToken)
        elif cur.isnumeric():
            newToken, line = tokenizeNumeric(line)
            tokens.append(newToken)
        elif cur == '"':
            newToken, line = tokenizeString(line)
            tokens.append(newToken)
        elif cur == '{':
            newToken = Token(TokenType.LeftBrace, cur)
            line = line[1:]
            tokens.append(newToken)
        elif cur == '}':
            newToken = Token(TokenType.RightBrace, cur)
            line = line[1:]
            tokens.append(newToken)
        elif cur == '(':
            newToken = Token(TokenType.LeftParentheses, cur)
            line = line[1:]
            tokens.append(newToken)
        elif cur == ')':
            newToken = Token(TokenType.RightParentheses, cur)
            line = line[1:]
            tokens.append(newToken)
        elif cur == '>':
            if len(line) > 1 and line[1] == '=':
                newToken = Token(TokenType.Geq, ">=")
                line = line[2:]
                tokens.append(newToken)
            else:
                newToken = Token(TokenType.Greater, cur)
                line = line[1:]
                tokens.append(newToken)
        elif cur == '<':
            if len(line) > 1 and line[1] == '=':
                newToken = Token(TokenType.Leq, "<=")
                line = line[2:]
                tokens.append(newToken)
            else:
                newToken = Token(TokenType.Less, cur)
                line = line[1:]
                tokens.append(newToken)
        elif cur == '=':
            newToken = Token(TokenType.Equal, cur)
            line = line[1:]
            tokens.append(newToken)
        elif cur == '∃':
            newToken = Token(TokenType.Exist, cur)
            line = line[1:]
            tokens.append(newToken)
        elif cur == '∀':
            newToken = Token(TokenType.Every, cur)
            line = line[1:]
            tokens.append(newToken)
        elif cur == '¬':
            newToken = Token(TokenType.Neg, cur)
            line = line[1:]
            tokens.append(newToken)
        elif cur == '-':
            newToken = Token(TokenType.Imply, "->")
            line = line[2:]
            tokens.append(newToken)
        elif cur == '.':
            newToken = Token(TokenType.Dot, cur)
            line = line[1:]
            tokens.append(newToken)
        elif cur == '∧':
            newToken = Token(TokenType.And, cur)
            line = line[1:]
            tokens.append(newToken)
        elif cur == '∨':
            newToken = Token(TokenType.Or, cur)
            line = line[1:]
            tokens.append(newToken)
        elif cur == '|':
            newToken = Token(TokenType.Pipe, cur)
            line = line[1:]
            tokens.append(newToken)
        elif cur == '∈':
            newToken = Token(TokenType.Belong, cur)
            line = line[1:]
            tokens.append(newToken)            
        else:
            raise Exception("error happening at line #" + str(linenumber) + ": cannot tokenize " + line)
    return tokens

# Take a line as input, return a token + remainingLine
def tokenizeId(line):
    cur = line[0]
    assert(cur.islower())
    elements = []
    elements.append(cur)
    line = line[1:]
    # either keyword or identifier            
    while len(line) > 0:
        cur = line[0]
        if cur.isalpha() or cur == '_':
            line = line[1:]
            elements.append(cur)
        else:
            break
    value = "".join(elements)
    newToken = Token(TokenType.Id, value)
    return newToken, line

# Take a line as input, return a token + remainingLine
def tokenizeTuple(line):
    cur = line[0]
    assert(cur.isupper())
    elements = []
    elements.append(cur)
    line = line[1:]
    value = "".join(elements)
    newToken = Token(TokenType.Tuple, value)
    return newToken, line

# Take a line as input, return a token + remainingLine
def tokenizeNumeric(line):
    cur = str(line[0])
    assert(cur.isnumeric())
    elements = []
    elements.append(cur)
    line = line[1:]
    # either keyword or identifier            
    while len(line) > 0:
        cur = str(line[0])
        if cur.isnumeric():
            line = line[1:]
            elements.append(cur)
        else:
            break
    value = "".join(elements)
    newToken = Token(TokenType.Integer, value)
    return newToken, line

# Take a line as input, return a token + remainingLine
def tokenizeString(line):
    cur = str(line[0])
    assert(cur == '"')
    elements = []
    line = line[1:]
    # either keyword or identifier            
    while len(line) > 0:
        cur = line[0]
        if cur != '"':
            line = line[1:]
            elements.append(cur)
        else:
            line = line[1:]
            break
    value = "".join(elements)
    newToken = Token(TokenType.String, value)
    return newToken, line

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Please pass the file name as the first argument, for example: 'python lex.py input1.txt'")
    print("Processing file: ", sys.argv[1])
    f = open(sys.argv[1], "r", encoding='UTF-8')
    source = (f.read())
    tokens = getTokens(source)
    print("Finish tokenizing:")
    for token in tokens:
        print(token)
