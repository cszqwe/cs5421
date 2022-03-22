from trc import Formula
from trc import FormulaType
from trc import ConditionalFormula
from trc import AndFormula
from trc import OrFormula
from trc import NegFormula
from trc import ImplyFormula
from trc import ParenthesesFormula
from trc import Atom
from trc import Condition
from trc import SingleCondition
from trc import SingleConditionType
from trc import parseTrc
import lex


def normaliseConditionalFormular(inputConditioanlFor: ConditionalFormula):
    # TODO:这里需要判断universal sepecifier

    if not haveUniversalSpecifier(inputConditioanlFor.condition):
        return NormaliseFormula(inputConditioanlFor.formula)  #nomalize child Formula, recursively

    # TODO:1.先将两种都有的分成两半
    if not haveTwoKindsConditon(inputConditioanlFor.condition):   #only universal specifiers

    else:                                                         #have both universal and exist specifiers

    # TODO:2.将universal那边进行化简
    # TODO:3.将左右两边通过AndFormular结合起来
    return inputConditioanlFor

def eliminateUniversal(UniversalFormula: ConditionalFormula):  #TODO:需要等Shengze定义带否定的Condition


def haveTwoKindsConditon(inputConditionList:Condition) -> bool:
    haveExist = False
    haveUniversal = False
    singCon: SingleCondition
    for singCon in inputConditionList:
        if singCon.type == SingleConditionType.ExistCondition:
            haveExist = True
        if singCon.type == SingleConditionType.EveryCondition:
            haveUniversal = True;

    if haveExist and haveUniversal:
        return True
    else:
        return False

def haveUniversalSpecifier(inputConditionList:Condition) -> bool:
    haveUniversal = False
    singCon: SingleCondition
    for singCon in inputConditionList:
        if singCon.type == SingleConditionType.EveryCondition:
            haveUniversal = True;
    return haveUniversal

def seperateConditionalFormular(inputConditionalFor:ConditionalFormula):
    return inputConditionalFor


def normaliseAndFormula(inputAndFor: AndFormula):
    leftFormula = NormaliseFormula(inputAndFor.formulaLeft)
    rightFormula = NormaliseFormula(inputAndFor.formulaRight)
    return AndFormula(leftFormula, rightFormula)

def normaliseOrFormula(inputOrFor: OrFormula):
    leftFormula = NormaliseFormula(inputOrFor.formulaLeft)
    rightFormula = NormaliseFormula(inputOrFor.formulaRight)
    return OrFormula(leftFormula, rightFormula)

def normaliseNegFormula(inputNegFor: NegFormula): ##TODO：这里要判断下面的是不是parenttheseFormula或者Neg
    return inputNegFor

def normaliseImplyFormula(inputImplyFor: ImplyFormula):
    leftFormula = NegFormula(inputImplyFor.formulaLeft)
    outputFormula = OrFormula(leftFormula, inputImplyFor.formulaRight)
    return outputFormula

def normaliseParentheseFormula(inputParFor: ParenthesesFormula):
    return inputParFor

def normaliseAtom(inputAtom: Atom):
    return inputAtom

formulaNormaliseSwitch = {
    FormulaType.ConditionalFormula: normaliseConditionalFormular,
    FormulaType.AndFormula: normaliseAndFormula,
    FormulaType.OrFormula: normaliseOrFormula,
    FormulaType.NegFormula: normaliseNegFormula,
    FormulaType.ImplyFormula: normaliseImplyFormula,
    FormulaType.ParenthesesFormula: normaliseParentheseFormula,
    FormulaType.Atom: normaliseAtom
}

def NormaliseFormula(inputFormula: Formula) -> Formula:
    return formulaNormaliseSwitch[inputFormula.type](inputFormula)






if __name__ == "__main__":
    f = open("input1.txt", encoding='UTF-8')
    source = (f.read())
    tokens = lex.getTokens(source)
    print("Finish tokenizing:")
    for token in tokens:
        print(token)
    print("Start parsing")
    trc = parseTrc(tokens)
    print("Finish parsing")
    NTrc = NormaliseFormula(trc.formula)
    print("done")

    '''
    Try test
    '''
    print("Start try test")
    if NTrc.type == FormulaType.ConditionalFormula:
        c: SingleCondition   ##在IDE中指定局部变量的type的方法，用alt+Enter
        for c in NTrc.actualFormula.condition:
            print("----------")
            if c.type == SingleConditionType.ExistCondition:
                print("type: Exist")
            if c.type == SingleConditionType.EveryCondition:
                print("type: Universal")
            print("tuple:" +str(c.tuple.value))
