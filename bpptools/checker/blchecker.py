import time
import subprocess
from z3 import Int, Not, And, Or, Exists, Solver, set_option
from itertools import chain
from collections import Counter

from bpptools.model.logicfml import Formula, Atom, Neg, Conj, Disj, Imp, EX, EG, AF
from bpptools.model.bpp import BPP, BRule


def generate_one_trans(rule, old_state, new_state):
    '''constraint which builds a relation between two BPP states according to a BPP rule'''
    process_num = len(old_state)
    projs = []
    for j in range(process_num):
        if j == rule.left_index:
            projs.append(new_state[j] == old_state[j] - 1 + rule.trans_vector[j])
        else:
            projs.append(new_state[j] == old_state[j] + rule.trans_vector[j])
    return And(*projs)

def state_equal(state1, state2):
    '''constraint reflecting that two states are equal'''
    process_num = len(state1)
    projs = [ state1[i] == state2[i] for i in range(process_num) ]
    return And(*projs)

def gen_cstr(bpp:BPP, formula:Formula, state, bound_k:int, counter):
    '''construct constraints for checking bounded liveness'''
    op_name = type(formula).__name__
    process_num = bpp.number
    rules = bpp.rules
    
    # atom
    if op_name == "Atom":
        vector = formula.vector
        required = formula.required
        flow = 0
        for i in range(process_num):
            flow += state[i] * vector[i]
        cstr = flow >= required
        counter['Atom'] += 1
        return cstr
    # negation
    elif op_name == "Neg":
        counter['Neg'] += 1
        return Not(gen_cstr(bpp, formula.subFormula, state, bound_k, counter))
    # conjunction
    elif op_name == "Conj":
        # check two subformula respectively
        left_sub_cstr = gen_cstr(bpp, formula.left, state, bound_k, counter)
        right_sub_cstr = gen_cstr(bpp, formula.right, state, bound_k, counter)
        # the conjunction constraint 
        counter['Conj'] += 1
        return And(left_sub_cstr, right_sub_cstr)
    # EX
    elif op_name == "EX":
        action = formula.action
        new_state = [ Int('u{}_{}'.format(counter['state'], j)) for j in range(process_num) ]
        counter['state'] += 1

        # construction of T(s,t,a)
        all_possibles = []
        for rule in rules:
            # action constraint: the action in the formula EX<a> should equal the one in the rule
            act_cstr = action == rule.action
            counter['action'] += 1
            # if the rule is X -> alpha, then there should be at least one X in the current state
            enb_cstr = state[rule.left_index] >= 1
            counter['enable'] += 1
            # expressing the relation between an old state and a new one
            big_t_minus = generate_one_trans(rule, state, new_state)
            counter['big_t_minus'] += 1
            # conjunction of the three sub-constraints above
            psb_trans = And(act_cstr, enb_cstr, big_t_minus)
            counter['psb_trans'] += 1
            # record every possible transtion
            all_possibles.append(psb_trans)
        big_t = Or(*all_possibles)
        counter['big_t'] += 1

        # construction of the full constraint
        sub_cstr = gen_cstr(bpp, formula.subFormula, new_state, bound_k, counter)
        exist_cstr = Exists(new_state, And(big_t, sub_cstr))
        cstr = And(bound_k >= 1, exist_cstr)
        counter['exist'] += 1
        counter['EX'] += 1
        return cstr
    # EG
    elif op_name == "EG":
        # generate k + 1 new states
        new_states = []
        for j in range(bound_k + 1):
            new_state = [ Int('u{}_{}'.format(counter['state'], j)) for j in range(process_num) ]
            counter['state'] += 1
            new_states.append(new_state)

        # Part 1. the first state in the path should equal the given state 
        first_equal = state_equal(new_states[0], state)
        counter['equal'] += 1

        # Part 2. construction of path constraint
        big_conjs = []
        for j in range(1, bound_k + 1):
            big_disjs = []
            for rule in rules:
                # if the rule is X -> alpha, then there should be at least one X in the current state
                enb_cstr = new_states[j-1][rule.left_index] >= 1
                counter['enable_eg'] += 1
                # expressing the relation between an old state and a new one
                big_t_minus = generate_one_trans(rule, new_states[j-1], new_states[j])
                counter['big_t_minus_eg'] += 1
                # conjunction of the three sub-constraints above
                disj = And(enb_cstr, big_t_minus)
                counter['disj'] += 1
                big_disjs.append(disj)
            # construction of the big disjunction
            disjs_cstr = Or(*big_disjs)
            counter['disjs_cstr'] += 1
            # record every conjunct
            big_conjs.append(disjs_cstr)
        conjs_cstr = And(*big_conjs)
        counter['conjs_cstr'] += 1

        # Part 3. construction of the conjunction of sub-constraints
        sub_cstrs = []
        for j in range(bound_k + 1):
            sub_cstr = gen_cstr(bpp, formula.subFormula, new_states[j], bound_k, counter)
            sub_cstrs.append(sub_cstr)
        sub_cstrs_conj = And(*sub_cstrs)
        counter['sub_cstrs_conj'] += 1

        # the final constraint
        variables = list(chain.from_iterable(new_states))
        cstr = Exists(variables, And(first_equal, conjs_cstr, sub_cstrs_conj))
        counter['EG'] += 1
        return cstr


def gen_cstr_d1(bpp:BPP, formula:Formula, state, bound_k:int, counter, solver):
    '''construct constraints for checking bounded liveness -- d1 formula version'''
    op_name = type(formula).__name__
    process_num = bpp.number
    rules = bpp.rules
    
    if op_name == "EX":
        action = formula.action
        new_state = [ Int('u{}_{}'.format(counter['state'], j)) for j in range(process_num) ]
        counter['state'] += 1

        # k should be at least 1
        k_ge_1 = And(bound_k >= 1)
        solver.assert_and_track(k_ge_1, "kGe1")
        
        # construction of T(s, t, a)
        all_possibles = []
        for rule in rules:
            # action constraint: the action in the formula EX<a> should equal the one in the rule
            act_cstr = action == rule.action
            # if the rule is X -> alpha, then there should be at least one X in the current state
            enb_cstr = state[rule.left_index] >= 1
            # expressing the relation between an old state and a new one
            big_t_minus = generate_one_trans(rule, state, new_state)
            # conjunction of the three sub-constraints above
            psb_trans = And(act_cstr, enb_cstr, big_t_minus)
            # record every possible transtion
            all_possibles.append(psb_trans)
        big_t = Or(*all_possibles)
        solver.assert_and_track(big_t, "connect")

        # construction of the conjunction of sub-constraints
        prop_cstr = gen_cstr(bpp, formula.subFormula.get_equivalent(), new_state, bound_k, counter)    
        solver.assert_and_track(prop_cstr, "prop")


    # EG
    if op_name == "EG":
        # generate k + 1 new states
        new_states = []
        for j in range(bound_k + 1):
            new_state = [ Int('u{}_{}'.format(counter['state'], j)) for j in range(process_num) ]
            counter['state'] += 1
            new_states.append(new_state)

        # Part 1. the first state in the path should equal the given state 
        solver.assert_and_track(state_equal(new_states[0], state), "equal")

        # Part 2. construction of path constraint
        for j in range(1, bound_k + 1):
            big_disjs = []
            for rule in rules:
                # if the rule is X -> alpha, then there should be at least one X in the current state
                enb_cstr = new_states[j-1][rule.left_index] >= 1
                # expressing the relation between an old state and a new one
                big_t_minus = generate_one_trans(rule, new_states[j-1], new_states[j])
                # conjunction of the three sub-constraints above
                disj = And(enb_cstr, big_t_minus)
                big_disjs.append(disj)
            # construction of the big disjunction
            disjs_cstr = Or(*big_disjs)
            solver.assert_and_track(disjs_cstr, "connect{}".format(j))

        # Part 3. construction of the conjunction of sub-constraints
        for j in range(bound_k + 1):
            prop_cstr = gen_cstr(bpp, formula.subFormula.get_equivalent(), new_states[j], bound_k, counter)
            solver.assert_and_track(prop_cstr, "prop{}".format(j))


class BLChecker:
    def __init__(self, ccfg, formula, bound_k):
        self.bpp = ccfg.convert()  
        self.formula = ccfg.aq2atom(formula)
        self.bound_k = bound_k
        self.initial_state = self.bpp.start_vector
        self.counter = Counter()
        self.solver = Solver()
        self.non_nested = self.bpp.check_fml(self.formula)

    def add_cstr(self):
        gen_cstr_d1(self.bpp, self.formula.get_equivalent(), self.initial_state, self.bound_k, self.counter, self.solver)

    def get_cstr(self):
        return gen_cstr(self.bpp, self.formula.get_equivalent(), self.initial_state, self.bound_k, self.counter)

    def check(self):
        if self.non_nested:
            self.add_cstr()
            return self.solver.check()
        else:
            cstr = self.get_cstr()
            self.solver.add(cstr)
            result = self.solver.check()
            return result

    def get_z3_statistics(self):
        return self.solver.statistics()

    def get_cstr_statistics(self):
        return self.counter

    def get_model(self):
        try:
            m = self.solver.model()
            return sorted([(d, m[d]) for d in m], key = lambda x: str(x[0]))
        except Exception as e:
            print(e)

    def get_unsat_core(self):
        try:
            return self.solver.unsat_core()
        except Exception as e:
            print(e)

    def get_assertions(self):
        set_option(max_args=10000000, max_lines=1000000, max_depth=10000000, max_visited=1000000)
        assertions = str(self.solver.assertions())
        return assertions

    # def write_assertions(self):
    #     set_option(max_args=10000000, max_lines=1000000, max_depth=10000000, max_visited=1000000)
    #     assertions = repr(self.solver.assertions())
    #     file_name = "assertions-{}.txt".format(time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime()))
    #     with open(file_name, 'w+') as f:
    #         for a in assertions:
    #             f.write(a)


if __name__ == "__main__":
    pass