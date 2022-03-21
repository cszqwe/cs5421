import sys
from enum import Enum, auto
from lex import Token
from lex import TokenType
import lex

class Trc():
    def __init__(self, tuple, formula):
        self.tuple = tuple
        self.formula = formula

def parseTrc(inputTokens): # inputTokens: []Token
    tokens = inputTokens.copy() # avoid modifying the original tokens
    assert(tokens[0].getType() == TokenType.LeftBrace)
    tokens = tokens[1:]
    tuple = parseTuple(tokens)
    tokens = tokens[1:]
    assert(tokens[0].getType() == TokenType.Pipe)
    tokens = tokens[1:]
    formula = parseFormula(tokens[:-1])
    assert(tokens[-1].getType() == TokenType.RightBrace)
    return Trc(tuple, formula)    

def parseFormula(inputTokens): # inputTokens: []Token
    #debugTokens(inputTokens)
    tokens = inputTokens.copy() # avoid modifying the original tokens
    # We go through the whole tokens list, check whether there exists a OrToken, and this should be a OrFormula.
    layer = 0
    foundOr = -1
    for i in range(len(tokens)):
        token = tokens[i]
        if token.getType() == TokenType.LeftParentheses:
            layer += 1
        elif token.getType() == TokenType.RightParentheses:
            layer -= 1
        elif token.getType() == TokenType.Or:
            if layer == 0:
                foundOr = i
                break
    if foundOr != -1:
        leftFormula = parseFormula(tokens[:foundOr])
        rightFormula = parseFormula(tokens[foundOr+1:])
        actualFormula = OrFormula(leftFormula, rightFormula)
        return Formula(FormulaType.OrFormula, actualFormula)

    # We go through the whole tokens list, check whether there exists a AndToken, and this should be a AndFormula.
    layer = 0
    foundAnd = -1
    for i in range(len(tokens)):
        token = tokens[i]
        if token.getType() == TokenType.LeftParentheses:
            layer += 1
        elif token.getType() == TokenType.RightParentheses:
            layer -= 1
        elif token.getType() == TokenType.And:
            if layer == 0:
                foundAnd = i
                break
    if foundAnd != -1:
        leftFormula = parseFormula(tokens[:foundAnd])
        rightFormula = parseFormula(tokens[foundAnd+1:])
        actualFormula = AndFormula(leftFormula, rightFormula)
        return Formula(FormulaType.AndFormula, actualFormula)

    # We go through the whole tokens list, check whether there exists a implyToken, and this should be a ImplyFormula.
    layer = 0
    foundImply = -1
    for i in range(len(tokens)):
        token = tokens[i]
        if token.getType() == TokenType.LeftParentheses:
            layer += 1
        elif token.getType() == TokenType.RightParentheses:
            layer -= 1
        elif token.getType() == TokenType.Imply:
            if layer == 0:
                foundImply = i
                break
    if foundImply != -1:
        leftFormula = parseFormula(tokens[:foundImply])
        rightFormula = parseFormula(tokens[foundImply+1:])
        actualFormula = ImplyFormula(leftFormula, rightFormula)
        return Formula(FormulaType.ImplyFormula, actualFormula)

    # If not the above cases, then we can just look at the first token, and determine the formula type.
    if tokens[0].getType() == TokenType.Exist or tokens[0].getType() == TokenType.Every:
        actualFormula = parseConditionFormula(tokens)
        return Formula(FormulaType.ConditionalFormula, actualFormula)
    elif tokens[0].getType() == TokenType.Neg:
        actualFormula = parseNegFormula(tokens)
        return Formula(FormulaType.NegFormula, actualFormula)
    elif tokens[0].getType() == TokenType.LeftParentheses:
        actualFormula = parseParenthesesFormula(tokens)
        return Formula(FormulaType.ParenthesesFormula, actualFormula)
    else:
        atom = parseAtom(tokens)
        return Formula(FormulaType.Atom, atom)

def parseConditionFormula(inputTokens):
    #debugTokens(inputTokens)
    tokens = inputTokens.copy()
    conditionList = []
    while tokens[0].getType() == TokenType.Exist or tokens[0].getType() == TokenType.Every:
        assert(tokens[1].getType() == TokenType.Tuple)
        if tokens[0].getType() == TokenType.Exist:
            singleCondition = SingleCondition(SingleConditionType.ExistCondition, parseTuple(tokens[1:]))
            conditionList.append(singleCondition)
        else:
            singleCondition = SingleCondition(SingleConditionType.EveryCondition, parseTuple(tokens[1:]))
            conditionList.append(singleCondition)
        tokens = tokens[2:]
    remainingFormula = parseFormula(tokens)
    return ConditionalFormula(conditionList, remainingFormula) 

def parseNegFormula(inputTokens):
    assert(inputTokens[0].getType() == TokenType.Neg)
    return parseFormula(inputTokens[1:])

def parseParenthesesFormula(inputTokens):
    assert(inputTokens[0].getType() == TokenType.LeftParentheses)
    rightParentheses = -1
    for i in range(len(inputTokens)):
        if inputTokens[i].getType() == TokenType.RightParentheses:
            rightParentheses = i
            break
    return ParenthesesFormula(parseFormula(inputTokens[1:rightParentheses]))

def parseAtom(inputTokens):
    #debugTokens(inputTokens)
    for token in inputTokens:
        if token.getType() == TokenType.Belong:
            return parseBelongAtom(inputTokens)
    return parseBopAtom(inputTokens)

def parseBelongAtom(inputTokens):
    tokens = inputTokens.copy()
    tuple = parseTuple(tokens)
    tokens = tokens[1:]
    #print("debug3", tokens[0].getType())
    assert(tokens[0].getType() == TokenType.Belong)
    tokens = tokens[1:]
    assert(tokens[0].getType() == TokenType.Id)
    tableName = TableName(tokens[0].getValue())
    return TypeAtom(tuple, tableName)

def parseBopAtom(inputTokens):
    left, remainingTokens = parseTupleAttributeOrConstant(inputTokens)
    assert(remainingTokens[0].getType() == TokenType.Geq or remainingTokens[0].getType() == TokenType.Leq or remainingTokens[0].getType() == TokenType.Greater or remainingTokens[0].getType() == TokenType.Less or remainingTokens[0].getType() == TokenType.Equal)
    bop = Bop(remainingTokens[0].getValue())
    right, remainingTokens = parseTupleAttributeOrConstant(remainingTokens[1:])
    assert(len(remainingTokens) == 0)
    return CompareAtom(left, bop, right)

def parseTupleAttributeOrConstant(inputTokens):
    tokens = inputTokens.copy()
    if tokens[0].getType() == TokenType.Integer:
        return TupleAttributeOrConstant(TupleAttributeOrConstantType.Constant, constant = Constant(ConstantType.Int, tokens[0].getValue())), tokens[1:]
    elif tokens[0].getType() == TokenType.String:
        return TupleAttributeOrConstant(TupleAttributeOrConstantType.Constant, constant = Constant(ConstantType.String, tokens[0].getValue())), tokens[1:]
    else:
        #debugTokens(inputTokens)
        assert(tokens[0].getType() == TokenType.Tuple)
        tuple = parseTuple(tokens)
        tokens = tokens[1:]
        assert(tokens[0].getType() == TokenType.Dot)
        tokens = tokens[1:]
        assert(tokens[0].getType() == TokenType.Id)
        attribute = Attribute(tokens[0].getValue())
        return TupleAttributeOrConstant(TupleAttributeOrConstantType.TupleAttribute, tupleAttribute = TupleAttribute(tuple, attribute)), tokens[1:]
                         
class Tuple():
    def __init__(self, value):
        assert(value.isupper())
        self.value = value

def parseTuple(inputTokens): # inputTokens: []Token
    return Tuple(inputTokens[0].getValue())

class FormulaType(Enum):
    ConditionalFormula = auto()
    AndFormula = auto()
    OrFormula = auto()
    NegFormula = auto()
    ImplyFormula = auto()
    ParenthesesFormula = auto()
    Atom = auto()
    
class Formula():
    def __init__(self, type, actualFormula):
        self.type = type
        self.actualFormula = actualFormula

class ConditionalFormula():
    def __init__(self, condition, formula):
        self.condition = condition
        self.formula = formula

class Condition():
    def __init__(self, conditionList): #conditionList: []SingleCondition
        self.conditionList = conditionList

class SingleConditionType(Enum):
    ExistCondition = auto()
    EveryCondition = auto()

class SingleCondition():
    def __init__(self, type, tuple):
        self.type = type
        self.tuple = tuple

class AndFormula():
    def __init__(self, formulaLeft, formulaRight):
        self.formulaLeft = formulaLeft
        self.formulaRight = formulaRight

class OrFormula():
    def __init__(self, formulaLeft, formulaRight):
        self.formulaLeft = formulaLeft
        self.formulaRight = formulaRight

class NegFormula():
    def __init__(self, formula):
        self.formula = formula
        
class ParenthesesFormula():
    def __init__(self, formula):
        self.formula = formula

class ImplyFormula():
    def __init__(self, formulaLeft, formulaRight):
        self.formulaLeft = formulaLeft
        self.formulaRight = formulaRight

class AtomType(Enum):
    CompareAtom = auto()
    TypeAtom = auto()

class Atom():
    def __init__(self, type, actualAtom):
        self.type = type
        self.actualAtom = actualAtom

class TupleAttributeOrConstantType(Enum):
    TupleAttribute = auto()
    Constant = auto() 

class TupleAttributeOrConstant():
    def __init__(self, type, tupleAttribute = None, constant = None): # type : TupleAttributeOrConstantType, tupleAttribute : TupleAttribute, constant : Constant
        self.type = type
        self.tupleAttribute = tupleAttribute
        self.constant = constant

class ConstantType(Enum):
    Int = auto()
    String = auto()

class Constant():
    def __init__(self, type, value): # type : ConstantType, value: String/Int
        self.type = type
        self.value = value

class TupleAttribute():
    def __init__(self, tuple, attribute): # tuple: Tuple, attribute: Attribute
        self. tuple = tuple
        self.attribute = attribute

class Attribute():
    def __init__(self, value): # value : String
        self.value = value

class Bop():
    def __init__(self, value): # value : String
        self.value = value

class CompareAtom():
    def __init__(self, left, bop, right): # left : TupleAttributeOrConstant, right: TupleAttributeOrConstant, bop : Bop
        self.left = left
        self.bop = bop
        self.right = right

class TableName():
    def __init__(self, value): # value : String
        self.value = value

class TypeAtom():
    def __init__(self, tuple, tableName): # tuple : Tuple, tableName: TableName
        self.tuple = tuple
        self.tableName = tableName

def debugTokens(tokens):
    print("BeginDebugTokens")
    for token in tokens:
        print(token.getValue())
    print("EndDebugTokens")
    
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Please pass the file name as the first argument, for example: 'python parse.py input1.txt'")
    else:
        print("Processing file: ", sys.argv[1])
        f = open(sys.argv[1], encoding='UTF-8')
        source = (f.read())
        tokens = lex.getTokens(source)
        print("Finish tokenizing:")
        for token in tokens:
            print(token)
        print("Start parsing")
        trc = parseTrc(tokens)
        print("Finish parsing")
