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
import trc
from trc import parseTrc
from trc import FormulaType,TupleAttributeOrConstantType,SingleConditionType,ConstantType
import lex
from normalisation import NormaliseFormula
from trc_print import printTrc
import copy
import os

# translate
def translate(TRC):
    norm_type = need_normalise(TRC)
    if len(norm_type) != 0:
        print('Normalisation is needed!\n', norm_type)
        return None
        
    f = TRC.formula
    ta,ta_atoms = find_tupleAttr(TRC)
    
    SQL = translate_cond(f,ta,ta_atoms,'')
    SQL += ';'
    return SQL

# Detect the format of TRC and decide whether a normalisation is needed
def need_normalise(TRC):
    norm_type = []
    
    if len(scan(TRC.formula,FormulaType.ImplyFormula,[])) != 0:
        norm_type.append('Implication formula exists!')
        
    conds = scan(TRC.formula,FormulaType.ConditionalFormula,[])
    for cond in conds:
        singlecond = cond.condition
        #if len(singlecond) > 1:
        #    norm_type.append('Multiple SingleCondition in one ConditionalFormula!')
        for sc in singlecond:
            if sc.type == SingleConditionType.EveryCondition:
                norm_type.append('EveryCondition formula exists!')
                
    negs = scan(TRC.formula,FormulaType.NegFormula,[])            
    for neg in negs:
        if neg.type == FormulaType.ParenthesesFormula:
            neg = neg.actualFormula.formula
        if neg.type == FormulaType.NegFormula:
            norm_type.append('Double Negtion exists!')
        elif neg.type != FormulaType.Atom:
            norm_type.append('Neg Formula exists!')

    return norm_type

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
    from_list = []
    conds = formula.actualFormula.condition
    for cond in conds:
        from_list.append(cond.tuple.value)
        
    tables = find_atom(scan(formula,FormulaType.Atom,[]),trc.TypeAtom) 
    tables_need = []
    for idx,i in enumerate(tables):
        if i.tuple.value in from_list:
            tables_need.append(tables[idx])
    if len(tables_need) > 1:
        for i in tables_need[:-1]:
            SQL += i.tableName.value +' '+ i.tuple.value + ', '
    SQL += tables_need[len(tables_need)-1].tableName.value +' '+ tables_need[len(tables_need)-1].tuple.value 
    
    SQL += '\nWHERE '
    SQL = translate_in_cond(formula.actualFormula.formula,SQL,ta_atoms) 
    
    return SQL

# deal with the parentheses formula under the condition
def translate_in_cond(formula,SQL,ta_atoms):
    if formula.type == FormulaType.ConditionalFormula: 
        assert (len(formula.actualFormula.condition) == 1)
        if formula.actualFormula.condition[0].type == SingleConditionType.ExistCondition:
            SQL += 'EXISTS'
        else:
            SQL += 'NOT EXISTS'
        SQL = translate_cond(formula,[],ta_atoms,SQL)
        SQL += ')'
    elif formula.type == FormulaType.ParenthesesFormula:
        formula = formula.actualFormula.formula
        SQL = translate_in_cond(formula,SQL,ta_atoms)
    elif formula.type == FormulaType.AndFormula:
        SQL = translate_rel(formula,'AND',SQL,ta_atoms)         
    elif formula.type == FormulaType.OrFormula:
         SQL = translate_rel(formula,'OR',SQL,ta_atoms)
         
    return SQL

# translate and/or Formula
def translate_rel(formula,rel,SQL,ta_atoms):
    left = formula.actualFormula.formulaLeft
    right = formula.actualFormula.formulaRight

    # Eliminate neg for CompareAtom
    if left.type == FormulaType.NegFormula:
        if left.type == FormulaType.ParenthesesFormula:
            left = left.actualFormul.formula
        left = left.actualFormula
        assert(isinstance(left.actualFormula,trc.CompareAtom))
        left.actualFormula = neg_bop(left.actualFormula)
    if right.type == FormulaType.NegFormula:
        if right.type == FormulaType.ParenthesesFormula:
            right = right.actualFormul.formula
        right = right.actualFormula
        assert(isinstance(right.actualFormula,trc.CompareAtom))
        right.actualFormula = neg_bop(right.actualFormula)
    
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
        parenthese = False
        if formula.type == FormulaType.ParenthesesFormula:
            SQL += '('
            parenthese = True
        SQL = translate_in_cond(formula,SQL,ta_atoms)
        if parenthese:
            SQL += ')'
    elif left.type != FormulaType.Atom and right.type == FormulaType.Atom:
        if not isinstance(right.actualFormula, trc.TypeAtom) and right.actualFormula not in ta_atoms: 
            SQL += ta_c_tostr(right.actualFormula)
            SQL += '\n' + rel+ ' '
        formula = formula.actualFormula.formulaLeft
        parenthese = False
        if formula.type == FormulaType.ParenthesesFormula:
            parenthese = True
            SQL += '('
        SQL = translate_in_cond(formula,SQL,ta_atoms)
        if parenthese:
            SQL += ')'
    else: 
        origin_formula = copy.deepcopy(formula)
        formula = origin_formula.actualFormula.formulaLeft
        parenthese = False
        if formula.type == FormulaType.ParenthesesFormula:
            parenthese = True
            SQL += '('
        SQL = translate_in_cond(formula,SQL,ta_atoms)
        if parenthese:
            SQL += ')'
        
        SQL += '\n' + rel + ' '
        formula = origin_formula.actualFormula.formulaRight
        parenthese = False
        if formula.type == FormulaType.ParenthesesFormula:
            parenthese = True
            SQL += '('
        SQL = translate_in_cond(formula,SQL,ta_atoms)
        if parenthese:
            SQL += ')'
    return SQL

# Negate CompareAtom
def neg_bop(compareAtom):
    if compareAtom.bop.value == '=':
        compareAtom.bop.value = '!='
    elif compareAtom.bop.value == '!=':
        compareAtom.bop.value == '='
    elif compareAtom.bop.value == '>':
        compareAtom.bop.value = '<='
    elif compareAtom.bop.value == '>=':
        compareAtom.bop.value = '<'
    elif compareAtom.bop.value == '<':
        compareAtom.bop.value = '>='
    elif compareAtom.bop.value == '<=':
        compareAtom.bop.value = '>'
    else:
        print('Wrong Binary Operator!')
    return compareAtom

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

# change TupleAttributeOrConstant to a string 
def ta_c_tostr(compare_atom):
    string = ''
    assert (isinstance(compare_atom , trc.CompareAtom))
    if compare_atom.left.type == TupleAttributeOrConstantType.TupleAttribute:
        string += compare_atom.left.tupleAttribute.tuple.value + '.' + compare_atom.left.tupleAttribute.attribute.value
    else:
        if compare_atom.left.constant.type == ConstantType.Int:
            string += str(compare_atom.left.constant.value)
        else:
            string += '\'' + str(compare_atom.left.constant.value) + '\''
    string += ' ' + compare_atom.bop.value + ' '
    if compare_atom.right.type == TupleAttributeOrConstantType.TupleAttribute:
        string += compare_atom.right.tupleAttribute.tuple.value + '.' + compare_atom.right.tupleAttribute.attribute.value
    else:
        if compare_atom.right.constant.type == ConstantType.Int:
            string += str(compare_atom.right.constant.value)
        else:
            string += '\'' + str(compare_atom.right.constant.value) + '\''
    return string

if __name__ == "__main__":
    # if len(sys.argv) < 3:
    #     print("Please pass the input file name as the first argument and output file name as the second argument,\
    #           for example: 'python translation.py input1.txt output1.txt'")
    # else:
    #     print("Processing file: ", sys.argv[1])
    #     f = open(sys.argv[1], encoding='UTF-8')
    
        # f = open('test case/trc_normalization_2.txt',encoding='UTF-8')
        # source = (f.read())
        # tokens = lex.getTokens(source)
        # TRC = parseTrc(tokens)
    
        # norm_type = need_normalise(TRC)
        # while(len(norm_type) != 0):
        #     #print(norm_type)
        #     TRC.formula = NormaliseFormula(TRC.formula)
        #     norm_type = need_normalise(TRC)
      
        # printTrc(TRC)
        
        # # test translate
        # SQL = translate(TRC)
        # print(SQL)
    
    files= os.listdir('test case')
    for file in files:
        name = file.split ("_", 1)
        if name[0] == 'sql':
            continue
        f = open('test case/'+file,encoding = 'UTF-8')
        source = (f.read())
        tokens = lex.getTokens(source)
        TRC = parseTrc(tokens)
        
        norm_type = need_normalise(TRC)
        while(len(norm_type) != 0):
            #print(norm_type)
            TRC.formula = NormaliseFormula(TRC.formula)
            norm_type = need_normalise(TRC)
      
        
        #printTrc(TRC)
        
        # test translate
        SQL = translate(TRC)
        print(SQL)
        
        with open('output/'+'output_'+file, 'w') as fw:
            fw.write(SQL)

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
             
        # test neg_bop
        # atoms = scan(TRC.formula,FormulaType.Atom,[])
        # cas = find_atom(atoms,trc.CompareAtom)
        # print(cas[0].bop.value)
        # print(neg_bop(cas[0]).bop.value)
        
        
        
        
        