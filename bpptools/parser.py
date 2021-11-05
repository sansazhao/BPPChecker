from lark import Lark

from bpptools.model.ccfg import Rule, CCFG
from bpptools.model.logicfml import Query, Neg, Conj, Disj, Imp, EX, AX, EG, AF, EF

GRAMMAR_FILE_PATH = "bpptools/problem.lark"

def parse_rea(rea):
    ccfg, query = rea.children
    ccfg_input = parse_ccfg(ccfg)
    query_input = parse_query(query)
    return ccfg_input, query_input

def parse_ccfg(ccfg):
    symbols, rules = ccfg.children
    initial = parse_symbols(symbols, [])
    rules_input = parse_rules(rules, [])
    return CCFG(initial, rules_input)

def parse_symbols(symbols, symbols_input):
    if symbols.data == "single":
        symbols_input.append(str(symbols.children[0]))
    else:
        for child in symbols.children:
            parse_symbols(child, symbols_input)
    return symbols_input

def parse_rules(rules, rules_input):
    if rules.data == "single":
        rules_input.append(parse_a_rule(rules.children[0]))
    else:
        for child in rules.children:
            parse_rules(child, rules_input)
    return rules_input

def parse_a_rule(rule):
    left = str(rule.children[0])
    if rule.data == "u_rule":
        right = parse_symbols(rule.children[1], [])
        return Rule(left, right)
    else:
        action = str(rule.children[1])
        right = parse_symbols(rule.children[2], [])
        return Rule(left, right, action)
    
def parse_query(query):
    acc, compare, num = query.children  
    acc_dict = {}
    parse_acc(acc, acc_dict)
    query_input = Query(acc_dict, str(compare), int(num))
    return query_input

def parse_acc(acc, acc_dict, connect=""):
    if acc.data == "single":
        parse_mult(acc.children[0], acc_dict, connect)
    elif acc.data == "multiple":
        for child in acc.children:
            if child == "-" or child == "+":
                connect = child
            else:
                parse_acc(child, acc_dict, connect)
    else:
        raise SyntaxError("Unknown acc type: {}".format(acc.data))

def parse_mult(mult, acc_dict, connect):
    var = str(mult.children[0])
    if mult.data == "one":
        num = 1
    elif mult.data == "coef":
        num = int(mult.children[1])
    else:
        raise SyntaxError("Unknown mult type: {}".format(mult.data))

    if connect == "-":
        acc_dict[var] = num * (-1)
    else:
        acc_dict[var] = num
        
def parse_bl(bl):
    ccfg, formula = bl.children
    ccfg_input = parse_ccfg(ccfg)
    formula_input = parse_formula(formula)
    return ccfg_input, formula_input

def parse_formula(formula):
    if formula.data == "atom":
        return parse_query(formula.children[0])
    elif formula.data == "unary":
        op = str(formula.children[0])
        sub = parse_formula(formula.children[1])
        if op == "Neg":
            return Neg(sub)
        elif op == "EG":
            return EG(sub)
        elif op == "AF":
            return AF(sub)
        elif op == "EF":
            return sub
    elif formula.data == "binary":
        left = parse_formula(formula.children[1])
        right = parse_formula(formula.children[2])
        op = str(formula.children[0])
        if op == "Conj":
            return Conj(left, right)
        elif op == "Disj":
            return Disj(left, right)
        elif op == "Imp":
            return Imp(left, right)
    elif formula.data == "next":
        action = str(formula.children[1])
        sub = parse_formula(formula.children[2])
        op = str(formula.children[0])
        if op == "EX":
            return EX(action, sub)
        elif op == "AX":
            return AX(action, sub)

def get_parse_tree(text):
    with open(GRAMMAR_FILE_PATH) as grammar_file:
        lark_parser = Lark(grammar_file)
        parse_tree = lark_parser.parse(text)
    return parse_tree
