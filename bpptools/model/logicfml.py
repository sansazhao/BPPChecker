from abc import ABCMeta, abstractmethod

class IllegalOp(Exception):
    '''Exception raised when the operation in a reachability query is not in the six operations ["==", "!=", ">", "<", ">=", "<="]'''
    pass


#########################################
#
# Formula
#
#########################################
class Formula(metaclass=ABCMeta):
    @abstractmethod
    def get_equivalent(self):
        pass


#########################################
#
# Query
#
#########################################
class Query(Formula):
    '''reachability query'''
    def __init__(self, acc, op, value):
        if not isinstance(acc, dict):
            raise TypeError('Expected a dict')
        for key in acc:
            if not isinstance(key, str):
                raise TypeError('Expected a string')
            if not isinstance(acc[key], int):
                raise TypeError('Expected an integer')

        if not isinstance(op, str):
            raise TypeError('Expected a string')
        if op not in ["==", "!=", ">", "<", ">=", "<="]:
            raise IllegalOp

        if not isinstance(value, int):
            raise TypeError('Expected an integer')
        self._acc = acc
        self._op = op
        self._value = value

    @property
    def acc(self):
        return self._acc

    @property
    def op(self):
        return self._op

    @property
    def value(self):
        return self._value

    def get_equivalent(self):
        return self

    def __repr__(self):
        return "Query({}, {}, {})".format(self._acc, self._op, self._value)

    def __str__(self):
        flow = []
        for k, v in self._acc.items():
            if v == 0:
                continue
            elif v == 1:
                flow.append("{}".format(k))
            else:
                flow.append("{} * {}".format(k, v))
        return "{} {} {}".format(" + ".join(flow), self._op, self._value)


#########################################
#
# Atom
#
#########################################
class Atom(Formula):
    def __init__(self, vector, op, required):
        if not isinstance(vector, list):
            raise TypeError('Expected a list')
        for v in vector:
            if not isinstance(v, int):
                raise TypeError('Expected a list of integers')
        
        if not isinstance(op, str):
            raise TypeError('Expected a string')
        if op not in ["==", "!=", ">", "<", ">=", "<="]:
            raise IllegalOp
        
        if not isinstance(required, int):
            raise TypeError('Expected an integer')
        self._vector = vector
        self._op = op
        self._required = required
    
    @property
    def vector(self):
        return self._vector

    @property
    def op(self):
        return self._op

    @property
    def required(self):
        return self._required

    def get_equivalent(self):
        return self

    def __repr__(self):
        return "Atom({}, {})".format(self._vector, self._required)

    def __str__(self):
        left_exp_list = []
        for p in enumerate(self._vector):
            if p[1] == 0:
                continue
            elif p[1] == 1:
                left_exp_list.append("X_{}".format(p[0]))
            else:
                left_exp_list.append("X_{} * {}".format(p[0], p[1]))
        left_exp = " + ".join(left_exp_list)
        return "{} {} {}".format(left_exp, self._op, self._required)


#########################################
#
# UnaryOpFormula
#
#########################################
class UnaryOpFormula(Formula):
    def __init__(self, subFormula):
        if not isinstance(subFormula, Formula):
            raise TypeError('Expected a formula')
        self._subFormula = subFormula
        
    @property
    def subFormula(self):
        return self._subFormula

    def __repr__(self):
        return "{}({})".format(type(self).__name__, self._subFormula.__repr__())

    def pretty_print(self, depth:int) -> str:
        name = type(self).__name__
        if isinstance(self._subFormula, Atom) or isinstance(self._subFormula, Query):
            sub = "|   " * depth + "-> " + self._subFormula.__str__()
        else:
            sub = "|   " * depth + "-> " + self._subFormula.pretty_print(depth + 1)
        return name + "\n" + sub

    def __str__(self):
        return self.pretty_print(1)


#########################################
#
# Neg
#
#########################################
class Neg(UnaryOpFormula):
    def get_equivalent(self):
        new_sub = self.subFormula.get_equivalent()
        return Neg(new_sub)


#########################################
#
# EG
#
#########################################
class EG(UnaryOpFormula):
    def get_equivalent(self):
        new_sub = self.subFormula.get_equivalent()
        return EG(new_sub)


#########################################
#
# AF
#
#########################################
class AF(UnaryOpFormula):
    def get_equivalent(self):
        new_sub = self.subFormula.get_equivalent()
        neg_sub = Neg(new_sub)
        return Neg(EG(neg_sub))

#########################################
#
# EF
#
#########################################
class EF(UnaryOpFormula):
    def get_equivalent(self):
        new_sub = self.subFormula.get_equivalent()
        return EF(new_sub)


#########################################
#
# Next
#
#########################################
class Next(Formula):
    def __init__(self, action, subFormula):
        if not isinstance(action, str):
            raise TypeError('Expected a str')
        if not isinstance(subFormula, Formula):
            raise TypeError('Expected a formula')
        self._action = action
        self._subFormula = subFormula

    @property
    def action(self):
        return self._action

    @property
    def subFormula(self):
        return self._subFormula

    def __repr__(self):
        return "{0}<{1}>({2})".format(type(self).__name__, self._action, self._subFormula.__repr__())

    def pretty_print(self, depth:int) -> str:
        name = type(self).__name__
        if isinstance(self._subFormula, Atom) or isinstance(self._subFormula, Query):
            sub = "|   " * depth + "-> " + self._subFormula.__str__()
        else:
            sub = "|   " * depth + "-> " + self._subFormula.pretty_print(depth + 1)
        return name + "<{}>".format(self._action) + "\n" + sub

    def __str__(self):
        return self.pretty_print(1)


#########################################
#
# EX
#
#########################################
class EX(Next):
    def get_equivalent(self):
        new_sub = self.subFormula.get_equivalent()
        return EX(self.action, new_sub)


#########################################
#
# AX
#
#########################################
class AX(Next):
    def get_equivalent(self):
        new_sub = self.subFormula.get_equivalent()
        neg_sub = Neg(new_sub)
        return Neg(EX(self.action, neg_sub))


#########################################
#
# BinaryOpFormula
#
#########################################
class BinaryOpFormula(Formula):
    def __init__(self, left, right):
        if not isinstance(left, Formula):
            raise TypeError('Expected a formula')
        if not isinstance(right, Formula):
            raise TypeError('Expected a formula')
        self._left = left
        self._right = right
    
    @property
    def left(self):
        return self._left

    @property
    def right(self):
        return self._right

    def __repr__(self):
        return "{0}({1}, {2})".format(type(self).__name__, self._left.__repr__(), self._right.__repr__())

    def pretty_print(self, depth:int) -> str:
        name = type(self).__name__
        if isinstance(self._left, Atom) or isinstance(self._left, Query):
            part1 = "|   " * depth + "-> " + self._left.__str__()
        else:
            part1 = "|   " * depth + "-> " + self.left.pretty_print(depth + 1)
        if isinstance(self._right, Atom) or isinstance(self._right, Query):
            part2 = "|   " * depth + "-> " + self._right.__str__()
        else:
            part2 = "|   " * depth + "-> " + self.right.pretty_print(depth + 1)
        return name + "\n" + part1 + "\n" + part2

    def __str__(self):
        return self.pretty_print(1)


#########################################
#
# Conj
#
#########################################
class Conj(BinaryOpFormula):
    def get_equivalent(self):
        new_left = self.left.get_equivalent()
        new_right = self.right.get_equivalent()
        return Conj(new_left, new_right)


#########################################
#
# Disj
#
#########################################
class Disj(BinaryOpFormula):
    def get_equivalent(self):
        new_left = self.left.get_equivalent()
        neg_left = Neg(new_left)
        new_right = self.right.get_equivalent()
        neg_right = Neg(new_right)
        return Neg(Conj(neg_left, neg_right))


#########################################
#
# Imp
#
#########################################
class Imp(BinaryOpFormula):
    def get_equivalent(self):
        left = self.left.get_equivalent()
        right = self.right.get_equivalent()
        neg_right = Neg(right)
        return Neg(Conj(left, neg_right))

