from trc import Formula, ConditionalFormula, TypeAtom, TupleAttributeOrConstant
from trc import FormulaType
from trc import ConditionalFormula
from trc import AndFormula
from trc import OrFormula
from trc import ImplyFormula
from trc import ParenthesesFormula
from trc import SingleCondition
from trc import SingleConditionType
from trc import CompareAtom
from trc import TypeAtom
from trc import TupleAttributeOrConstant
from trc import TupleAttributeOrConstantType
from trc import Tuple
from trc import TupleAttribute
from trc import Constant
from trc import Trc
from trc import parseTrc
from normalisation import NormaliseFormula
import trc
import lex

# 1.Conditional Formula
def conFormulaToStr(inputConFormula: Formula) -> str:  #DONE
    if inputConFormula.type != FormulaType.ConditionalFormula:
        assert ("ERROR: conFormulaToStr - input Formula type is not FormulaType.ConditionalFormula")
        return ""
    actualConFor: ConditionalFormula = inputConFormula.actualFormula

    conditionsStr = ""
    singCon: SingleCondition
    for singCon in actualConFor.condition:
        conTypeStr = ""
        if singCon.type == SingleConditionType.EveryCondition:
            conTypeStr = "∀"
        elif singCon.type == SingleConditionType.ExistCondition:
            conTypeStr = "∃"
        elif singCon.type == SingleConditionType.NotExistConditon:
            conTypeStr = "¬∃"
        conditionsStr = conditionsStr + conTypeStr + singCon.tuple.value + ' '

    formulaStr = FormulaToStr(actualConFor.formula)
    return conditionsStr + formulaStr

# 2. And Formula
def andFormulaToStr(inputAndFormula: Formula) -> str:    #DONE
    if inputAndFormula.type != FormulaType.AndFormula:
        assert ("ERROR: andFormulaToStr - input Formula type is not FormulaType.AndFormula")
        return ""
    outputStr = ""

    actualAndFor: AndFormula = inputAndFormula.actualFormula
    left: Formula = actualAndFor.formulaLeft
    right: Formula = actualAndFor.formulaRight
    leftStr = '(' + FormulaToStr(left) + ')'
    rightStr = '(' + FormulaToStr(right) + ')'

    outputStr = leftStr + ' ' + '∧' + ' ' + rightStr
    return outputStr

# 3. Or Formula
def orFormulaToStr(inputOrFormula: Formula) -> str:    #DONE
    if inputOrFormula.type != FormulaType.OrFormula:
        assert ("ERROR: orFormulaToStr - input Formula type is not FormulaType.OrFormula")
        return ""
    outputStr = ""

    actualOrFor: OrFormula = inputOrFormula.actualFormula
    left: Formula = actualOrFor.formulaLeft
    right: Formula = actualOrFor.formulaRight
    leftStr = '(' + FormulaToStr(left) + ')'
    rightStr = '(' + FormulaToStr(right) + ')'

    outputStr = leftStr + ' ' + '∨' + ' ' + rightStr
    return outputStr

# 4. Neg Formula
def negFormulaToStr(inputNegFormula: Formula)->str:      #DONE
    if inputNegFormula.type != FormulaType.NegFormula:
        assert ("ERROR: negFormulaToStr - input Formula type is not FormulaType.OrFormula")
        return ""
    outputStr = ""
    innerFormulaStr = '(' + FormulaToStr(inputNegFormula.actualFormula) + ')'
    outputStr = '¬' + innerFormulaStr
    return outputStr

# 5. Imply Formula
def implyFormulaToStr(inputImplyFormula: Formula)->str:     #DONE
    if inputImplyFormula.type != FormulaType.ImplyFormula:
        assert ("ERROR: implyFormulaToSt - input Formula type is not FormulaType.ImplyFormula")
        return ""
    outputStr = ""

    actualImpyFor:ImplyFormula = inputImplyFormula.actualFormula
    leftStr = FormulaToStr(actualImpyFor.formulaLeft)
    rightStr = FormulaToStr(actualImpyFor.formulaRight)
    outputStr = leftStr + ' ' + "->" + ' ' + rightStr
    return outputStr

# 6. Parenthese Formula
def parentheseFormulaToStr(inputParentheseFormula: Formula)->str:   #DONE
    if inputParentheseFormula.type != FormulaType.ParenthesesFormula:
        assert ("ERROR: parentheseFormulaToStr - input Formula type is not FormulaType.ParenthesesFormula")
        return ""
    actualParentheseFor: ParenthesesFormula = inputParentheseFormula.actualFormula
    outputStr = '(' + FormulaToStr(actualParentheseFor.formula) + ')'
    return outputStr

# 7.Atom
def atomToStr(inputAtomFormula: Formula) -> str:   #DONE
    if inputAtomFormula.type != FormulaType.Atom:
        assert ("ERROR:  atomToStr - input Formula type is not FormulaType.Atom")
        return ""
    actualAtom = inputAtomFormula.actualFormula
    outputStr = ""
    # 1. compare atom
    '''
    <Atom> -> <CompareAtom>
    <CompareAtom> -> <TupleAttributeOrConstant> <Bop> <TupleAttributeOrConstant>
    <TupleAttributeOrConstant> -> <TupleAttribute>
    <TupleAttribute> -> <Tuple>.<AttributeName>
    <AttributeName> -> <Identifier>
    <TupleAttributeOrConstant> -> <Constant>
    <Constant> -> int
    <Constant> -> string
    '''
    if isinstance(actualAtom, CompareAtom):
        actualCompareAtom = actualAtom
        left: TupleAttributeOrConstant = actualCompareAtom.left
        right: TupleAttributeOrConstant = actualCompareAtom.right

        leftStr = tupleAttributeOrConstantToStr(left)
        rightStr = tupleAttributeOrConstantToStr(right)
        bopStr = actualCompareAtom.bop.value

        outputStr = leftStr + ' ' + bopStr + ' ' + rightStr
    # 2. type atom
    '''
    <Atom> -> <TypeAtom>
    <TypeAtom> -> <Tuple> ∈ <TableName>
    <TableName> -> <Identifier>
    <Identifier> -> [a-z][a-zA-Z]+
    '''
    if isinstance(actualAtom, TypeAtom):
        actualTypeAtom: TypeAtom = actualAtom
        tupleStr = actualTypeAtom.tuple.value
        tableNameStr = actualTypeAtom.tableName.value
        outputStr = tupleStr + ' ' + '∈' + ' ' + tableNameStr
    return outputStr

def tupleAttributeOrConstantToStr(inpuAttrOrCons: TupleAttributeOrConstant) -> str:
    if inpuAttrOrCons.type == TupleAttributeOrConstantType.TupleAttribute:
        inputTupleAttr: TupleAttribute = inpuAttrOrCons.tupleAttribute
        return inputTupleAttr.tuple.value + '.' + inputTupleAttr.attribute.value
    elif inpuAttrOrCons.type == TupleAttributeOrConstantType.Constant:
        inputConstant: Constant = inpuAttrOrCons.constant
        return str(inputConstant.value)
    else:
        assert ("ERROR:  tupleAttributeOrConstantToStr - input type is not TupleAttribute or Constant")
        return ""



formulaToStrSwitch = {
    FormulaType.ConditionalFormula: conFormulaToStr,
    FormulaType.AndFormula: andFormulaToStr,
    FormulaType.OrFormula: orFormulaToStr,
    FormulaType.NegFormula: negFormulaToStr,
    FormulaType.ImplyFormula: implyFormulaToStr,
    FormulaType.ParenthesesFormula: parentheseFormulaToStr,
    FormulaType.Atom: atomToStr
}


def FormulaToStr(inputFormula: Formula) -> str:
    return formulaToStrSwitch[inputFormula.type](inputFormula)

def TupleToStr(inputTuple: Tuple) -> str:
    return inputTuple.value

def TrcToStr(inputTrc: Trc) -> str:
    outputStr = ""

    tupleStr = TupleToStr(inputTrc.tuple)
    formulaStr = FormulaToStr(inputTrc.formula)
    outputStr = '{ ' + tupleStr + ' | ' + formulaStr + ' }'
    return outputStr

if __name__ == "__main__":
    # f = open("input1.txt", encoding='UTF-8')
    f = open("normalisation_test/test1_atom_parenthese_and.txt", encoding='UTF-8')
    source = (f.read())
    tokens = lex.getTokens(source)
    print("Finish tokenizing:")
    for token in tokens:
        print(token)
    print("Start parsing")
    originalTrc = parseTrc(tokens)  # TODO:trc.py处理implication 好像有点问题
    print("Finish parsing")



    Ntrc = NormaliseFormula(originalTrc.formula)
    # test---------------
    # 1. Conditional Formula    done
    # 2. And Formula            done
    # 3. Or Formula             done
    # 4. Neg Formula            done
    # 5. Imply Formula          done
    # 6. Parentnese Formula     done
    # 7. Atom                   done
    print("test done")


    print("start print trc formula")
    trcFormulaStr = TrcToStr(originalTrc)
    print(trcFormulaStr)

    print("Finish print trc formula")
