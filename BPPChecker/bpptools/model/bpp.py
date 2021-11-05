from bpptools.model.logicfml import Atom, UnaryOpFormula, Next, BinaryOpFormula


class LeftIndexLessThanZero(Exception):
    '''Exception raised when the left index in a BPP rule is less than zero''' 
    pass


class NegativeInVec(Exception):
    '''Exception raised when the trans_vector in a BPP rule contains a negative integer''' 
    pass


class NonStrAction(Exception):
    '''Exception raised when the action in a labelled BPP rule is not a string''' 
    pass


#########################################
#
# Rule
#
#########################################
class BRule:
    '''BPP rules'''
    def __init__(self, left_index, trans_vector, action=""):
        if not isinstance(left_index, int):
            raise TypeError('Expected an integer')
        if left_index < 0:
            raise LeftIndexLessThanZero

        if not isinstance(trans_vector, list):
            raise TypeError('Expected a list')
        for value in trans_vector:
            if not isinstance(value, int):
                raise TypeError('Expected a list of integers')
            if value < 0:
                raise NegativeInVec

        if not isinstance(action, str):
            raise NonStrAction
        self._left_index = left_index
        self._trans_vector = trans_vector
        self._action = action

    @property
    def left_index(self):
        return self._left_index

    @property
    def trans_vector(self):
        return self._trans_vector

    @property
    def action(self):
        return self._action

    def __repr__(self):
        return "Rule({0}, '{1}', {2})".format(self._left_index, self._action, self._trans_vector)

    def __str__(self):
        res = "X_{} -> '{}' -> ".format(self._left_index, self._action)
        projs = [ "X_{} * {}".format(i, self._trans_vector[i]) for i in range(len(self._trans_vector)) if (self._trans_vector[i] != 0) ]
        return res + "(" + ", ".join(projs) + ")"


class NumOfProcsLessThanZero(Exception):
    '''Exception raised when the number of processes in a BPP is less than zero'''
    pass


class StartVecLenNotMatch(Exception):
    '''Exception raised when the length of the start vector is not consistent with the number of processes in a BPP'''
    pass


class EmptyListOfRules(Exception):
    '''Exception raised when a BPP contains no rule'''
    pass


class InconsistentRules(Exception):
    '''Exception raised when a BPP contains rules with different types'''
    pass


class NagativeStartVec(Exception):
    '''Exception raised when the start vector in a BPP contains a negative integer''' 
    pass


class NeedAtom(Exception):
    '''Exception raised when the innermost formula is not an Atom formula'''
    pass


class IllegalAtomFormula(Exception):
    '''Exception raised when the length of the vector of an Atom formula is not consistent with the number of processes in a BPP'''
    pass


class RuleVecLenNotMatch(Exception):
    '''Exception raised when the length of the trans_vector of a BPP rule is not consistent with the number of processes in a BPP'''
    def __init__(self, number, rule, length):
        super().__init__(number, rule, length)
        self.number = number
        self.rule = rule
        self.length = length
    def __str__(self):
        return "The number of variables of the BPP is {0}, but the length of rule vector in {1} is {2}.".format(self.number, self.rule, self.length)


#########################################
#
# BPP
#
#########################################
class BPP:
    def __init__(self, number, start_vector, rules):        
        if not isinstance(number, int):
            raise TypeError('Expected an integer')
        if number < 0:
            raise NumOfProcsLessThanZero

        if not isinstance(start_vector, list):
            raise TypeError('Expected a list')
        for value in start_vector:
            if not isinstance(value, int):
                raise TypeError('Expected a list of integers')
            if value < 0:
                raise NagativeStartVec
        if len(start_vector) != number:
            raise StartVecLenNotMatch
        
        rule_type_name = None
        if len(rules) == 0:
            raise EmptyListOfRules
        else:
            rule_type_name = type(rules[0]).__name__
            for rule in rules:
                if not isinstance(rule, BRule):
                    raise TypeError('Expected a rule')
                if not type(rule).__name__ == rule_type_name:
                    raise InconsistentRules
                if len(rule.trans_vector) != number:
                    raise RuleVecLenNotMatch(number, rule, len(rule.trans_vector))
        self._number = number
        self._start_vector = start_vector
        self._rules = rules
    
    @property
    def number(self):
        return self._number

    @property
    def start_vector(self):
        return self._start_vector

    @property
    def rules(self):
        return self._rules

    def check_fml(self, formula):
        '''check whether an EG formula is a legal formula for bounded model checking liveness, returning a boolean value representing whether this is a formula without nested temporal operators'''
        if not (hasattr(formula, 'subFormula') 
            or hasattr(formula, 'left') 
            or isinstance(formula, Atom)):
            raise NeedAtom

        op_name = type(formula).__name__
        if op_name == "AX" or op_name == "AF":
            self.check_fml(formula.subFormula)
            return False

        if op_name == "EX" or op_name == "EG":
            return self.check_fml(formula.subFormula)
        elif op_name == "Atom":
            if not len(formula.vector) == self.number:
                raise IllegalAtomFormula
            return True
        elif op_name == "Neg":
            sub = formula.subFormula
            self.check_fml(sub)
            sub_name = type(sub).__name__
            if sub_name == "EX" or sub_name == "EG":
                return False
            else:
                return True
        else:
            left = formula.left
            right = formula.right
            left_name = type(left).__name__
            right_name = type(right).__name__
            left_res = self.check_fml(left)
            right_res = self.check_fml(right)
            if left_name == "EX" or left_name == "EG" or right_name == "EX" or right_name == "EG":
                return False
            else:
                return left_res and right_res

    def start_state(self):
        projs = [ "X_{0} * {1}".format(i, self._start_vector[i]) for i in range(len(self._start_vector)) if (self._start_vector[i] != 0) ]
        return "(" + ", ".join(projs) + ")"
    
    def __repr__(self):
        rule_repr = [ rule.__repr__() for rule in self._rules ]
        return "LabelledBPP({0}, {1}, [{2}])".format(self._number, self._start_vector, ', '.join(rule_repr))

    def __str__(self):
        separate = "=" * 30
        claim_number = "This BPP contains {0} variable{1}.\n".format(self._number, "s" if self._number else "")
        claim_start = "The starting state: \n" + self.start_state() + "\n"
        claim_rules = "The set of rules:"
        for rule in self._rules:
            claim_rules += "\n" + rule.__str__()
        return separate + "\n" + claim_number + claim_start + claim_rules + "\n" + separate

