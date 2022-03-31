from trc import Formula, ConditionalFormula
from trc import FormulaType
from trc import ConditionalFormula
from trc import AndFormula
from trc import OrFormula
from trc import ImplyFormula
from trc import ParenthesesFormula
from trc import SingleCondition
from trc import SingleConditionType
import trc as tc

from trc import parseTrc
import lex

# global variable: iteration times(1 or not)
flag = True
def change_flag():
    global flag
    flag = False

# helper functions------------------------------------------------

# Scan on the trc and find the FormulaType. Return a list of formula objects.
def scan(formula,target,objects):
    if target == formula.type:
        objects.append(formula.actualFormula)
        if formula.type == FormulaType.ConditionalFormula or formula.type == FormulaType.ParenthesesFormula:
                objects = scan(formula.actualFormula.formula,target,objects)
        elif formula.type == FormulaType.AndFormula or formula.type == FormulaType.OrFormula:
            objects = scan(formula.actualFormula.formulaLeft,target,objects)
            objects = scan(formula.actualFormula.formulaRight,target,objects)
    else:
        if formula.type == FormulaType.ConditionalFormula or formula.type == FormulaType.ParenthesesFormula:
                objects = scan(formula.actualFormula.formula,target,objects)
        elif formula.type == FormulaType.AndFormula or formula.type == FormulaType.OrFormula:
            objects = scan(formula.actualFormula.formulaLeft,target,objects)
            objects = scan(formula.actualFormula.formulaRight,target,objects)
    return objects

# find all CompareAtom or TypeAtom 
def find_atom(atoms_list,target):
    objects = []
    for atom in atoms_list:
        if isinstance(atom,target):
            objects.append(atom)
    return objects


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

# 1. Conditional Formula: ∀t F(t) => (¬∃t) ¬F(t)
def normaliseConFormularWrapper(inputConFor: Formula) -> Formula:
    if inputConFor.type != FormulaType.ConditionalFormula:
        assert("ERROR: normaliseConFormularWrapper - input Formula type is not FormulaType.ConditionalFormula")
        return inputConFor
    actualConFor: ConditionalFormula = inputConFor.actualFormula

    # 1. convert multi condition formula to nested conditional formula
    actualConFor = multiConditionForToNest(actualConFor)

    # 2. normalise
    actualConFor = normaliseConFormular(actualConFor)

    return Formula(FormulaType.ConditionalFormula, actualConFor)

def normaliseConFormular(inputConFor: ConditionalFormula) -> ConditionalFormula:
    # the input must be nested conditional formula
    singCon = inputConFor.condition[0]
    tempConFor: ConditionalFormula = inputConFor

    # 1. if in this layer, the condition is universal, normalise it
    if singCon.type == SingleConditionType.EveryCondition:
        # convert condition part
        convertedNotExistSingCon = SingleCondition(SingleConditionType.NotExistConditon, singCon.tuple)
        convertedCondition = [convertedNotExistSingCon]

        # convert formula part
        convertedNegFormula = Formula(FormulaType.NegFormula, inputConFor.formula)
        tempConFor = ConditionalFormula(convertedCondition, convertedNegFormula)

    # 2. recrusively normalise the sub formula
    tempConFor = normaliseConForSubFormula(tempConFor)
    return tempConFor


# 2. AndFormula
def normaliseAndFormulaWrapper(inputAndFor: Formula) -> Formula:
    if inputAndFor.type != FormulaType.AndFormula:
        assert("ERROR:normaliseAndFormulaWrapper - input Formula type is not FormulaType.AndFormula")
        return inputAndFor
    return Formula(FormulaType.AndFormula, normaliseAndFormula(inputAndFor))

def normaliseAndFormula(inputAndFor: AndFormula) -> AndFormula:  #Done
    leftFormula: Formula = NormaliseFormula(inputAndFor.actualFormula.formulaLeft)
    rightFormula: Formula = NormaliseFormula(inputAndFor.actualFormula.formulaRight)
    return AndFormula(leftFormula, rightFormula)



# 3. OrFormula
def normaliseOrFormulaWrapper(inputOrFor: Formula) -> Formula:
    if inputOrFor.type != FormulaType.OrFormula:
        assert("ERROR:normaliseOrFormulaWrapper - input Formula type is not FormulaType.OrFormula")
        return inputOrFor
    return Formula(FormulaType.OrFormula, normaliseOrFormula(inputOrFor.actualFormula))

def normaliseOrFormula(inputOrFor: OrFormula) -> OrFormula:
    leftFormula = NormaliseFormula(inputOrFor.formulaLeft)
    rightFormula = NormaliseFormula(inputOrFor.formulaRight)
    return OrFormula(leftFormula, rightFormula)

# 4. NegFormula

def normaliseNegFormulaWrapper(inputNegFor: Formula) -> Formula:
    if inputNegFor.type != FormulaType.NegFormula:
        assert("ERROR:normaliseNegFormulaWrapper - input Formula type is not FormulaType.NegFormula")
        return inputNegFor

    innerFormula: Formula = inputNegFor.actualFormula
    innerFormulaType = innerFormula.type
    inputNegForWithoutParenthese: Formula = inputNegFor

    # 0.消除parenthese in the first iteration
    global flag
    if innerFormulaType == FormulaType.ParenthesesFormula and flag:
        innerFormula = innerFormula.actualFormula.formula
        inputNegForWithoutParenthese = Formula(FormulaType.NegFormula, innerFormula)
        innerFormulaType = innerFormula.type
        change_flag()


    #
    # 1. ¬¬F => F
    if innerFormulaType == FormulaType.NegFormula:
        normalisedThisLayerFormula =  innerFormula.actualFormula
        return NormaliseFormula(normalisedThisLayerFormula)

    # 2. ¬(F1 ∧ F2) =>  ¬F1 ∨ ¬F2
    elif innerFormulaType == FormulaType.AndFormula:
        innerActualAnd: AndFormula = innerFormula.actualFormula
        f1 = innerActualAnd.formulaLeft
        f2 = innerActualAnd.formulaRight
        leftNegFormula = Formula(FormulaType.NegFormula, f1)
        rightNegFormula = Formula(FormulaType.NegFormula, f2)
        actualOrFor = OrFormula(leftNegFormula, rightNegFormula)
        normalisedThisLayerFormula =  Formula(FormulaType.OrFormula, actualOrFor)
        return NormaliseFormula(normalisedThisLayerFormula)
    # 3. ¬(F1 ∨ F2) =>  ¬F1 ∧ ¬F2
    elif innerFormulaType == FormulaType.OrFormula:
        innerActualOr: OrFormula = innerFormula.actualFormula
        f1 = innerActualOr.formulaLeft
        f2 = innerActualOr.formulaRight
        leftNegFormula = Formula(FormulaType.NegFormula, f1)
        rightNegFormula = Formula(FormulaType.NegFormula, f2)
        actualAndFor = AndFormula(leftNegFormula, rightNegFormula)
        normalisedThisLayerFormula = Formula(FormulaType.AndFormula, actualAndFor)
        return NormaliseFormula(normalisedThisLayerFormula)

    # 4. ¬(ConditionalFormula)
    elif innerFormulaType == FormulaType.ConditionalFormula:
        condition = innerFormula.actualFormula.condition
        cond_new = []
        if condition[0].type == SingleConditionType.EveryCondition:
            normalisedSubFormula = NormaliseFormula(inputNegForWithoutParenthese.actualFormula)
            return Formula(FormulaType.NegFormula, normalisedSubFormula)
        elif condition[0].type == SingleConditionType.ExistCondition:
            cond_new.append(SingleCondition(SingleConditionType.NotExistConditon,condition[0].tuple))
        elif condition[0].type == SingleConditionType.NotExistConditon:
            cond_new.append(SingleCondition(SingleConditionType.ExistCondition,condition[0].tuple))
        NormalisedConditionalFormula = ConditionalFormula(cond_new, innerFormula.actualFormula.formula) 
        return NormaliseFormula(Formula(FormulaType.ConditionalFormula,NormalisedConditionalFormula))
    
    # 5. Iteration 1+ with Parentheses inside Neg
    elif innerFormulaType == FormulaType.ParenthesesFormula:
        innerFormula = innerFormula.actualFormula.formula
        inputNegForWithoutParenthese = Formula(FormulaType.NegFormula, innerFormula)
        normalisedSubFormula = NormaliseFormula(inputNegForWithoutParenthese.actualFormula)
        formula = Formula(FormulaType.NegFormula, normalisedSubFormula)
        outputFormula = NormaliseFormula(formula)
        return Formula(FormulaType.ParenthesesFormula,ParenthesesFormula(outputFormula))
    
    # 6. None of these above
    else:
        normalisedSubFormula = NormaliseFormula(inputNegForWithoutParenthese.actualFormula)
        return Formula(FormulaType.NegFormula, normalisedSubFormula)


# 5. ImplyFormula:
# F1->F2  =>  ¬F1 ∨ F2
def normaliseImplyFormulaWrapper(inputImplyFor: Formula) -> Formula:
    if inputImplyFor.type != FormulaType.ImplyFormula:
        assert("ERROR: normaliseImplyFormulaWrapper - input Formula type is not FormulaType.ImplyFormula")
        return inputImplyFor
    return Formula(FormulaType.OrFormula, normaliseImplyFormula(inputImplyFor.actualFormula))

def normaliseImplyFormula(inputImplyFor: ImplyFormula) -> OrFormula:
    leftFormula = Formula(FormulaType.NegFormula, inputImplyFor.formulaLeft)
    leftFormula = NormaliseFormula(leftFormula)
    rightFormula = NormaliseFormula(inputImplyFor.formulaRight)
    outputFormula = OrFormula(leftFormula, rightFormula)
    return outputFormula

# 6. ParentheseFormula
# delete Parenthese
def normaliseParentheseFormulaWrapper(inputParFor: Formula) -> Formula:
    if inputParFor.type != FormulaType.ParenthesesFormula:
        assert("ERROR: normaliseParentheseFormulaWrapper - input Formula type is not FormulaType.ParenthesesFormula")
        return inputParFor
    inner = inputParFor.actualFormula.formula
    typeAtoms = find_atom(scan(inner,FormulaType.Atom, []), tc.TypeAtom)
    if (inner.type == FormulaType.AndFormula or inner.type == FormulaType.OrFormula) \
        and len(typeAtoms) == 0:
        print('11111')
        from trc_print import printTrc
        print('TRC:')
        printTrc(tc.Trc(tc.Tuple('T'),inputParFor))
        formula = Formula(FormulaType.ParenthesesFormula,normaliseParentheseFormula(inputParFor.actualFormula))
        return formula
    else:
        return NormaliseFormula(inputParFor.actualFormula.formula)
    
def normaliseParentheseFormula(inputParentheseFor: ParenthesesFormula) -> ParenthesesFormula:
    outputFormula = NormaliseFormula(inputParentheseFor.formula)
    return ParenthesesFormula(outputFormula)

# 7. Atom
def normaliseAtom(inputAtomFormula: Formula) -> Formula:
    return inputAtomFormula

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



# some test
if __name__ == "__main__":
    #f = open("input1.txt", encoding='UTF-8')
    f = open("normalisation_test/test3_implication_exist.txt", encoding='UTF-8')
    source = (f.read())
    tokens = lex.getTokens(source)
    print("Finish tokenizing:")
    for token in tokens:
        print(token)
    print("Start parsing")
    trc = parseTrc(tokens)
    print("Finish parsing")
    Ntrc = NormaliseFormula(trc.formula)
    # test---------------
    # 1. Conditional Formula    done
    # 2. And Formula            done
    # 3. Or Formula             done
    # 4. Neg Formula            done
    # 5. Imply Formula          done
    # 6. Parentnese Formula     done
    # 7. Atom                   done
    print("test done")