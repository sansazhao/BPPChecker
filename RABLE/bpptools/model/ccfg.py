from collections import Counter
import re

from bpptools.model.bpp import BRule, BPP
from bpptools.model.logicfml import Query, Atom, UnaryOpFormula, Next, BinaryOpFormula


class IllegalString(Exception):
    '''Exception raised when a symbol is not a legal string (not matching an re pattern)'''
    pass


#########################################
#
# Rule
#
#########################################
class Rule:
    def __init__(self, left, right, action=""):
        def check_symbol(sb):
            if not isinstance(sb, str):
                raise TypeError('Expected a string')
            if not re.match(r'[a-zA-Z_]\w*', sb):
                raise IllegalString
        
        check_symbol(left)

        if not isinstance(action, str):
            raise TypeError('Expected a string')

        if not isinstance(right, list):
            raise TypeError('Expected a list')
        for sb in right:
            check_symbol(sb)
        self._left = left
        self._action = action
        self._right = right
        self._right_counter = Counter(self._right)

    @property
    def left(self):
        return self._left

    @property
    def action(self):
        return self._action

    @property
    def right(self):
        return self._right

    def symbol_num(self, symbol:str) -> int:
        return self._right_counter[symbol]

    def __repr__(self):
        return "Rule({0}, '{1}', {2})".format(self._left, self._action, self._right)

    def __str__(self):
        return "{0} --> '{1}' --> {2}".format(self._left, self._action, ' | '.join(self._right))


class EmptyListOfRules(Exception):
    '''Exception raised when a CCFG contains no rule'''
    pass


class NeedQuery(Exception):
    '''Exception raised when the innermost formula is not an Query formula'''
    pass


#########################################
#
# CCFG
#
#########################################
class CCFG:
    def __init__(self, initial, rules):
        if not isinstance(initial, list):
            raise TypeError('Expected a list')
        for sb in initial:
            if not isinstance(sb, str):
                raise TypeError('Expected a string')

        if not isinstance(rules, list):
            raise TypeError('Expected a list')
      
        if len(rules) == 0:
            raise EmptyListOfRules
        else:
            for r in rules:
                if not isinstance(r, Rule):
                    raise TypeError('Expected a rule')
        self._initial = initial
        self._rules = rules
        self._symbols = self.get_symbols()
        self._symbol_num = len(self._symbols)

    @property
    def initial(self):
        return self._initial

    @property
    def rules(self):
        return self._rules

    @property
    def symbols(self):
        return self._symbols

    def get_symbols(self):
        '''return all symbols in a CCFG'''
        symbols = set()
        for sb in self._initial:
            symbols.add(sb)
        for rule in self._rules:
            symbols.add(rule.left)
            for ter in rule.right:
                symbols.add(ter)
        return list(symbols)

    def symbol_rule_index_map(self):
        '''return a dict which maps a symbol to all rules containing the symbol; the mapping value of a symbol is a list of rule indexes'''
        rule_index = {}
        for sb in self._symbols:
            rule_index[sb] = [ i for i in range(len(self._rules)) if sb in self._rules[i].right ]
        return rule_index

    def convert(self):
        '''convert a CCFG to a VAS-form BPP'''
        number = len(self._symbols)
        start_vector = [ 1 if sb in self._initial else 0 for sb in self._symbols ]
        
        bpp_rules = []
        for rule in self._rules:
            left_index = self._symbols.index(rule.left)
            trans_vector = [ rule.right.count(sb) for sb in self._symbols ]
            action = rule.action
            bpp_rule = BRule(left_index, trans_vector, action)
            bpp_rules.append(bpp_rule)
        
        return BPP(number, start_vector, bpp_rules)

    def aq2atom(self, aq_formula):
        '''convert a formula whose innermost formula is of type Query to one whose innermost part is an Atom formula'''
        symbols = self._symbols
        fml_type = type(aq_formula)
        if not (hasattr(aq_formula, 'subFormula') 
            or hasattr(aq_formula, 'left') 
            or isinstance(aq_formula, Query)):
            raise NeedQuery

        if isinstance(aq_formula, Query):
            acc = aq_formula._acc
            vector = []
            for sb in symbols:
                try:
                    count = acc[sb]
                except KeyError:
                    vector.append(0)
                else:
                    vector.append(count)
            return Atom(vector, aq_formula.op, aq_formula.value)
        elif isinstance(aq_formula, UnaryOpFormula):
            return fml_type(self.aq2atom(aq_formula.subFormula))
        elif isinstance(aq_formula, Next):
            action = aq_formula.action
            return fml_type(action, self.aq2atom(aq_formula.subFormula))
        elif isinstance(aq_formula, BinaryOpFormula):
            left = self.aq2atom(aq_formula.left)
            right = self.aq2atom(aq_formula.right)
            return fml_type(left, right)

    def __repr__(self):
        return "CCFG('{}', [{}])".format(self._initial, ', '.join([ rule.__repr__() for rule in self._rules ]))

    def __str__(self):
        separate = "=" * 30
        claim_number = "This CCFG contains {} symbol{}.\n".format(self._symbol_num, "s" if self._symbol_num else "")
        claim_start = "The initial symbols: \n{}".format(self._initial) + "\n"
        claim_rules = "The set of rules:"
        for rule in self._rules:
            claim_rules += "\n" + rule.__str__()
        return separate + "\n" + claim_number + claim_start + claim_rules + "\n" + separate

