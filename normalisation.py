from trc import Formula, ConditionalFormula
from trc import FormulaType
from trc import ConditionalFormula
from trc import AndFormula
from trc import OrFormula
from trc import ImplyFormula
from trc import ParenthesesFormula
from trc import Atom
from trc import Condition
from trc import SingleCondition
from trc import SingleConditionType
import copy

from trc import parseTrc
import lex



# helper functions------------------------------------------------




def normaliseConForSubFormula(inputConditionalFor: ConditionalFormula) -> ConditionalFormula:
    subFormula = inputConditionalFor.formula
    return ConditionalFormula(inputConditionalFor.condition, NormaliseFormula(subFormula))


def multiConditionForToNest(inputConditionalFor: ConditionalFormula) -> ConditionalFormula:     #test done
    if len(inputConditionalFor.condition) <= 1:
        return inputConditionalFor

    innerCons = inputConditionalFor.condition[1:]
    innerConFor = ConditionalFormula(innerCons, inputConditionalFor.formula)
    innerConFor = multiConditionForToNest(innerConFor)       # recursively convert to nested conditional formula
    innerFormula = Formula(FormulaType.ConditionalFormula, innerConFor)

    outerCon = []
    outerCon.append(inputConditionalFor.condition[0])
    outerConFor = ConditionalFormula(outerCon, innerFormula)

    return outerConFor


# nomalisation functions-----------------------------------------------
# TODO：检查哪些需要递归normalise没写的

# 1. Conditional Formula: ∀t F(t) => (¬∃t) ¬F(t)
def normaliseConFormularWrapper(inputConFor: Formula) -> Formula:    #TODO: unit test
    if inputConFor.type != FormulaType.ConditionalFormula:
        assert("ERROR: normaliseConFormularWrapper - input Formula type is not FormulaType.ConditionalFormula")
        return inputConFor
    actualConFor: ConditionalFormula = inputConFor.actualFormula

    # 1. convert multi condition formula to nested conditional formula
    actualConFor = multiConditionForToNest(actualConFor)

    # 2. normalise
    actualConFor = normaliseConFormular(actualConFor)

    return Formula(FormulaType.ConditionalFormula, actualConFor)

def normaliseConFormular(inputConFor: ConditionalFormula) -> ConditionalFormula: #TODO: unit test
    # the input must be nested conditional formula
    singCon = inputConFor.condition[0]
    tempConFor: ConditionalFormula = inputConFor

    # 1. if in this layer, the condition is universal, normalise it
    if singCon.type == SingleConditionType.EveryCondition:
        # convert condition part
        convertedNotExistSingCon = SingleCondition(SingleConditionType.NotExistConditon, singCon.tuple)
        convertedCondition = Condition([convertedNotExistSingCon])    #TODO: need test

        # convert formula part
        convertedNegFormula = Formula(FormulaType.NegFormula, inputConFor.formula)
        tempConFor = ConditionalFormula(convertedCondition, convertedNegFormula)

    # 2. recrusively normalise the sub formula
    tempConFor = normaliseConForSubFormula(tempConFor)
    return tempConFor


# 2. AndFormula  #DONE #TODO: unit test
def normaliseAndFormulaWrapper(inputAndFor: Formula) -> Formula:
    if inputAndFor.type != FormulaType.AndFormula:
        assert("ERROR:normaliseAndFormulaWrapper - input Formula type is not FormulaType.AndFormula")
        return inputAndFor
    return Formula(FormulaType.AndFormula, normaliseAndFormula(inputAndFor))

def normaliseAndFormula(inputAndFor: AndFormula) -> AndFormula:  #Done
    leftFormula: Formula = NormaliseFormula(inputAndFor.actualFormula.formulaLeft)
    rightFormula: Formula = NormaliseFormula(inputAndFor.actualFormula.formulaRight)
    return AndFormula(leftFormula, rightFormula)



# 3. OrFormula  #DONE #TODO : unit test
def normaliseOrFormulaWrapper(inputOrFor: Formula) -> Formula:
    if inputOrFor.type != FormulaType.OrFormula:
        assert("ERROR:normaliseOrFormulaWrapper - input Formula type is not FormulaType.OrFormula")
        return inputOrFor
    return Formula(FormulaType.AndFormula, normaliseOrFormula(inputOrFor))

def normaliseOrFormula(inputOrFor: OrFormula) -> OrFormula:
    leftFormula = NormaliseFormula(inputOrFor.formulaLeft)
    rightFormula = NormaliseFormula(inputOrFor.formulaRight)
    return OrFormula(leftFormula, rightFormula)

# 4. NegFormula #TODO: unit test

def normaliseNegFormulaWrapper(inputNegFor: Formula) -> Formula:
    if inputNegFor.type != FormulaType.NegFormula:
        assert("ERROR:normaliseNegFormulaWrapper - input Formula type is not FormulaType.NegFormula")
        return inputNegFor

    innerFormula: Formula = inputNegFor.actualFormula
    innerFormulaType = innerFormula.type
    inputNegForWithoutParenthese: Formula = inputNegFor

    # 0.消除parenthese
    if innerFormulaType == FormulaType.ParenthesesFormula:
        innerFormula = innerFormula.actualFormula.formula
        inputNegForWithoutParenthese = Formula(FormulaType.NegFormula, innerFormula)
        innerFormulaType = innerFormula.type

    # 每次只消除一种：有两种选项
    # 1. 消除双的 DONE
    # ¬¬F => F
    if innerFormulaType == FormulaType.NegFormula:
        normalisedThisLayerFormula =  innerFormula.actualFormula
        return NormaliseFormula(normalisedThisLayerFormula)
    # 2. 消除sandwich， 定义：neg 里面是and或者or
    # 1) ¬(F1 ∧ F2) =>  ¬F1 ∨ ¬F2
    elif innerFormulaType == FormulaType.AndFormula:
        innerActualAnd: AndFormula = innerFormula.actualFormula
        f1 = innerActualAnd.formulaLeft
        f2 = innerActualAnd.formulaRight
        leftNegFormula = Formula(FormulaType.NegFormula, f1)
        rightNegFormula = Formula(FormulaType.NegFormula, f2)
        actualOrFor = OrFormula(leftNegFormula, rightNegFormula)
        normalisedThisLayerFormula =  Formula(FormulaType.OrFormula, actualOrFor)
        return NormaliseFormula(normalisedThisLayerFormula)
    # 2) ¬(F1 ∨ F2) =>  ¬F1 ∧ ¬F2
    elif innerFormulaType == FormulaType.OrFormula:
        innerActualOr: OrFormula = innerFormula.actualFormula
        f1 = innerActualOr.formulaLeft
        f2 = innerActualOr.formulaRight
        leftNegFormula = Formula(FormulaType.NegFormula, f1)
        rightNegFormula = Formula(FormulaType.NegFormula, f2)
        actualAndFor = OrFormula(leftNegFormula, rightNegFormula)
        normalisedThisLayerFormula = Formula(FormulaType.AndFormula, actualAndFor)
        return NormaliseFormula(normalisedThisLayerFormula)

    # 3.不是双也不是sandwich，就直接子normalise然后返回
    else:
        normalisedSubFormula = NormaliseFormula(inputNegForWithoutParenthese.actualFormula)
        return Formula(FormulaType.NegFormula, normalisedSubFormula)


# 5. ImplyFormula #TODO: unit test
def normaliseImplyFormulaWrapper(inputImplyFor: Formula) -> Formula: #DONE #TODO: unit test
    if inputImplyFor.type != FormulaType.ImplyFormula:
        assert("ERROR: normaliseImplyFormulaWrapper - input Formula type is not FormulaType.ImplyFormula")
        return inputImplyFor
    return Formula(FormulaType.OrFormula, normaliseImplyFormula(inputImplyFor.actualFormula))

def normaliseImplyFormula(inputImplyFor: ImplyFormula) -> OrFormula:   #TODO:这里没有包装
    leftFormula = Formula(FormulaType.NegFormula, inputImplyFor.formulaLeft)
    outputFormula = OrFormula(leftFormula, inputImplyFor.formulaRight)
    return outputFormula

# 6. ParentheseFormula #delete Parentese
def normaliseParentheseFormulaWrapper(inputParFor: Formula) -> Formula:   #TODO: unit test
    if inputParFor.type != FormulaType.ParenthesesFormula:
        assert("ERROR: normaliseParentheseFormulaWrapper - input Formula type is not FormulaType.ParenthesesFormula")
        return inputParFor
    actualParenteseFormula: ParenthesesFormula = inputParFor.actualFormula
    return NormaliseFormula(actualParenteseFormula.formula)

# 7. Atom
def normaliseAtom(inputAtomFormula: Formula) -> Formula:
    return inputAtomFormula


#TODO:改成wrapper
formulaNormaliseSwitch = {
    FormulaType.ConditionalFormula: normaliseConFormularWrapper,
    FormulaType.AndFormula: normaliseAndFormulaWrapper,
    FormulaType.OrFormula: normaliseOrFormulaWrapper,
    FormulaType.NegFormula: normaliseNegFormulaWrapper,
    FormulaType.ImplyFormula: normaliseImplyFormulaWrapper,
    FormulaType.ParenthesesFormula: normaliseParentheseFormulaWrapper,
    FormulaType.Atom: normaliseAtom
}



def NormaliseFormula(inputFormula: Formula) -> Formula:
    return formulaNormaliseSwitch[inputFormula.type](inputFormula)




if __name__ == "__main__":
    #f = open("input1.txt", encoding='UTF-8')
    f = open("normalisation_test/input_temp.txt", encoding='UTF-8')
    source = (f.read())
    tokens = lex.getTokens(source)
    print("Finish tokenizing:")
    for token in tokens:
        print(token)
    print("Start parsing")
    trc = parseTrc(tokens)
    print("Finish parsing")

    # normal test

    Ntrc = NormaliseFormula(trc.formula)


    # unit test---------------
    # TODO:测试的思路测试用例用同种的进行嵌套
    # 1. Conditional Formula
    # 2. And Formula   done
    # 3. Or Formula
    # 4. Neg Formula   done
    # 5. Imply Formula
    # 6. Parentnese Formula done
    # 7. Atom done
    print("unit test done")
