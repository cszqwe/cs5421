# -*- coding: utf-8 -*-
'''
Output: a txt file with SQL output inside  

String Form:
Keywords: in the following list(SQL Grammer, Relation).
Every keyword take a line.(There is a '\n' before every keyword.) 
SQL Grammer: {SELECT,FROM,WHERE}
Relation: {AND,OR}

Identifier: {EXISTS,NOT EXISTS}
Table names: [a-zA-Z]+
For all nested SELECT: SELECT *  

Other information refers to 'ProductionRuleForTRC.txt'
'''
import sys
import trc
from trc import parseTrc
from trc import FormulaType,TupleAttributeOrConstantType,SingleConditionType
import lex

# translate
def translate(TRC):
    if len(scan(TRC.formula,FormulaType.ImplyFormula,[])) != 0:
        print('Implication formula exists!')
        return None
    conds = scan(TRC.formula,FormulaType.ConditionalFormula,[])
    for cond in conds:
        singlecond = cond.condition
        for sc in singlecond:
            if sc.type == SingleConditionType.EveryCondition:
                print('EveryCondition formula exists!')
                return None
    negs = scan(TRC.formula,FormulaType.ConditionalFormula,[])            
    for neg in negs:
        inner = neg.formula.actualFormula
        if inner == FormulaType.NegFormula:
            print('Double Negtion exists!')
            return None
        
    f = TRC.formula
    ta,ta_atoms = find_tupleAttr(TRC)
    
    SQL = translate_cond(f,ta,ta_atoms,'')
    SQL += ';'
    return SQL

# separate based on conditional formula
def translate_cond(formula,ta,ta_atoms,SQL):
    assert(formula.type == FormulaType.ConditionalFormula)
    if len(ta) != 0:
        SQL += '\nSELECT '
        for i in ta[:-1]:
            SQL += i.tuple.value +'.'+ i.attribute.value + ','
        SQL += ta[len(ta)-1].tuple.value +'.'+ ta[len(ta)-1].attribute.value 
    else:
        SQL += '\n(SELECT *'
    
    SQL += '\nFROM '
    tables = find_atom(scan(formula,FormulaType.Atom,[]),trc.TypeAtom)
    # TODO: Compare with Singlecondition; now this is a redundant solution. 
    for i in tables[:-1]:
        SQL += i.tableName.value +' '+ i.tuple.value + ', '
    SQL += tables[len(tables)-1].tableName.value +' '+ tables[len(tables)-1].tuple.value 
    
    SQL += '\nWHERE '
    SQL = translate_in_cond(formula.actualFormula.formula,SQL,ta_atoms) 
    
    return SQL

# deal with the parentheses formula under the condition
def translate_in_cond(formula,SQL,ta_atoms):
    if formula.type == FormulaType.ConditionalFormula: 
        SQL += 'EXIST'
        SQL = translate_cond(formula.actualFormula,[],SQL)
        SQL += ')'
    elif formula.type == FormulaType.ParenthesesFormula:
        formula = formula.actualFormula.formula
        SQL = translate_in_cond(formula,SQL,ta_atoms)
    elif formula.type == FormulaType.NegFormula:
        # TODO: deal with neg atom 
        SQL += '\nNOT '
        formula = formula.actualFormula.formula
        SQL = translate_in_cond(formula,SQL,ta_atoms)
    elif formula.type == FormulaType.AndFormula:
        SQL = translate_rel(formula,'AND',SQL,ta_atoms)         
    elif formula.type == FormulaType.OrFormula:
         SQL = translate_rel(formula,'OR',SQL,ta_atoms)
    return SQL

# translate and/or
def translate_rel(formula,rel,SQL,ta_atoms):
    left = formula.actualFormula.formulaLeft
    right = formula.actualFormula.formulaRight
    if left.type == FormulaType.Atom and right.type == FormulaType.Atom:
        if not isinstance(left.actualFormula, trc.TypeAtom) and left.actualFormula not in ta_atoms: 
            SQL += ta_c_tostr(left.actualFormula)
            if not isinstance(right.actualFormula, trc.TypeAtom) and right.actualFormula not in ta_atoms:
                SQL += '\n' + rel + ' '
                SQL += ta_c_tostr(right.actualFormula)
        else:
            if not isinstance(right.actualFormula, trc.TypeAtom) and right.actualFormula not in ta_atoms:
                SQL += ta_c_tostr(right.actualFormula)
    elif left.type == FormulaType.Atom and right.type != FormulaType.Atom:
        if not isinstance(left.actualFormula, trc.TypeAtom) and left.actualFormula not in ta_atoms: 
            SQL += ta_c_tostr(left.actualFormula)
            SQL += '\n' + rel+ ' '
        formula = formula.actualFormula.formulaRight
        SQL = translate_in_cond(formula,SQL,ta_atoms)
    elif left.type != FormulaType.Atom and right.type == FormulaType.Atom:
        if not isinstance(right.actualFormula, trc.TypeAtom) and right.actualFormula not in ta_atoms: 
            SQL += ta_c_tostr(left.actualFormula)
            SQL += '\n' + rel+ ' '
        formula = formula.actualFormula.formulaLeft
        SQL = translate_in_cond(formula,SQL,ta_atoms)
    else: 
        formula = formula.actualFormula.formulaLeft
        SQL = translate_in_cond(formula,SQL,ta_atoms)
        formula = formula.actualFormula.formulaRight
        SQL = translate_in_cond(formula,SQL,ta_atoms)
    return SQL

# Find all of the TupleAttributes for SELECT. Return a list of TupleAttribute ta.
def find_tupleAttr(TRC):
    ta = []
    ta_atoms = []
    atoms = scan(TRC.formula,FormulaType.Atom,[])
    compare_atoms = find_atom(atoms,trc.CompareAtom)
    for atom in compare_atoms:
        bop = atom.bop
        left = atom.left
        right = atom.right
        if bop.value == '=' and left.type == TupleAttributeOrConstantType.TupleAttribute \
            and right.type == TupleAttributeOrConstantType.TupleAttribute:
                if left.tupleAttribute.tuple.value == TRC.tuple.value:
                    ta.append(right.tupleAttribute)
                    ta_atoms.append(atom)
                if right.tupleAttribute.tuple.value == TRC.tuple.value:
                    ta.append(left.tupleAttribute)
                    ta_atoms.append(atom)
    return ta,ta_atoms


# Scan on the trc and find the FormulaType. Return a list of formula objects.
def scan(formula,target,objects):
    if target == formula.type:
        objects.append(formula.actualFormula)
        if formula.type == FormulaType.ConditionalFormula or formula.type == FormulaType.NegFormula \
            or formula.type == FormulaType.ParenthesesFormula:
                objects = scan(formula.actualFormula.formula,target,objects)
        elif formula.type == FormulaType.AndFormula or formula.type == FormulaType.OrFormula:
            objects = scan(formula.actualFormula.formulaLeft,target,objects)
            objects = scan(formula.actualFormula.formulaRight,target,objects)
    else:
        if formula.type == FormulaType.ConditionalFormula or formula.type == FormulaType.NegFormula \
            or formula.type == FormulaType.ParenthesesFormula:
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

# change TupleAttributeOrConstant to a string 
def ta_c_tostr(compare_atom):
    string = ''
    assert (isinstance(compare_atom , trc.CompareAtom))
    if compare_atom.left.type == TupleAttributeOrConstantType.TupleAttribute:
        string += compare_atom.left.tupleAttribute.tuple.value + '.' + compare_atom.left.tupleAttribute.attribute.value
    else:
        string += str(compare_atom.left.constant.value)
    string += ' ' + compare_atom.bop.value + ' '
    if compare_atom.right.type == TupleAttributeOrConstantType.TupleAttribute:
        string += compare_atom.right.tupleAttribute.tuple.value + '.' + compare_atom.right.tupleAttribute.attribute.value
    else:
        string += str(compare_atom.right.constant.value)
    return string

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Please pass the input file name as the first argument and output file name as the second argument,\
              for example: 'python translation.py input1.txt output1.txt'")
    else:
        print("Processing file: ", sys.argv[1])
        f = open(sys.argv[1], encoding='UTF-8')
        source = (f.read())
        tokens = lex.getTokens(source)
        #for token in tokens:
        #    print(token)
        TRC = parseTrc(tokens)
        
        # test scan 
        # print(TRC.formula.actualFormula.formula.actualFormula.formula.actualFormula.formulaLeft)
        # print(scan(TRC.formula,FormulaType.ConditionalFormula,[]))
        # print(scan(TRC.formula,FormulaType.AndFormula,[]))
        # print(scan(TRC.formula,FormulaType.OrFormula,[]))
        # print(scan(TRC.formula,FormulaType.NegFormula,[]))
        # print(scan(TRC.formula,FormulaType.ParenthesesFormula,[]))
        # print(scan(TRC.formula,FormulaType.Atom,[]))
        # atoms = scan(TRC.formula,FormulaType.Atom,[])
        
        # test find_atom
        #print(find_atom(atoms,trc.TypeAtom))
        #print(find_atom(atoms,trc.CompareAtom))
        
        # test find_tupleAttr
        #ta = find_tupleAttr(TRC)
        #for t in ta:
        #    print(t.tuple.value,t.attribute.value)
        
        # test ta_c_tostr
        # atoms = scan(TRC.formula,FormulaType.Atom,[])
        # compare_atoms = find_atom(atoms,trc.CompareAtom)
        # for compare_atom in compare_atoms:
        #     print(ta_c_tostr(compare_atom))
        
        # test translate
        SQL = translate(TRC)
        print(SQL)
        with open(sys.argv[2], 'w') as fw:
            fw.write(SQL)
        
        
        
        
        
        