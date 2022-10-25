from z3 import Int, And, Or, Solver 
from collections import Counter
from functools import reduce

from bpptools.model.ccfg import Rule, CCFG

class RChecker:
    def __init__(self, ccfg, query, solver=Solver()):
        initial4solving = "ReaInit"
        new_initial = [initial4solving]
        new_rule = Rule(initial4solving, ccfg._initial)
        new_rules = [new_rule]
        for rule in ccfg.rules:
            new_rules.append(rule)
        self._ccfg = CCFG(new_initial, new_rules)
        self._query = query
        self.solver = solver
        self.symbols = self._ccfg.get_symbols()
        self.initial_sb = self._ccfg.initial[0]
        self.var_x_dict = self.get_var_dict()[0]
        self.var_z_dict = self.get_var_dict()[1]
        self.rule_num = len(self._ccfg.rules)
        self.rule_counter = [ Int("y{}".format(i)) for i in range(self.rule_num) ]
        self.result = None
    
    def get_var_dict(self):
        var_x_dict = {}
        var_z_dict = {}
        for sb in self.symbols:
            var_x_dict[sb] = Int("x_{}".format(sb))
            var_z_dict[sb] = Int("z_{}".format(sb))
        return var_x_dict, var_z_dict

    def add_basics(self):
        for sb in self.symbols:
            self.solver.assert_and_track(self.var_x_dict[sb] >= 0, "{}_ge0".format(sb))

        for var_y in self.rule_counter:
            self.solver.assert_and_track(var_y >= 0, "{}_ge0".format(var_y))

    def add_flow(self):
        for sb in self.symbols:
            if sb == self.initial_sb:
                flow = 1
            else:
                flow = 0

            for i in range(self.rule_num):
                rule = self._ccfg.rules[i]
                const = rule.symbol_num(sb)
                if rule.left == sb:
                    const = const - 1
                flow += const * self.rule_counter[i]

            var_x = self.var_x_dict[sb]
            self.solver.assert_and_track(var_x == flow, "{}_flow".format(sb))

    def add_connectivity(self):
        for sb in self.symbols:
            var_x = self.var_x_dict[sb]
            var_z = self.var_z_dict[sb]
            if not sb == self.initial_sb:
                self.solver.assert_and_track(Or(var_x == 0, var_z > 0), "{}_z_gt0".format(sb))

        rule_index = self._ccfg.symbol_rule_index_map()
        
        for sb in self.symbols:
            disjuncts = []
            indexes = rule_index[sb]
            var_z = self.var_z_dict[sb]

            not_gen = [var_z == 0]
            for index in indexes:
                not_gen.append(self.rule_counter[index] == 0)
            disjuncts.append(And(*not_gen))

            for index in indexes:
                var_y = self.rule_counter[index]
                rule = self._ccfg.rules[index]
                left_sb = rule.left
                if left_sb == self.initial_sb:
                    disj = And(var_z == 1, var_y > 0)
                else:
                    var_z_parent = self.var_z_dict[left_sb]
                    disj = And(var_z == var_z_parent + 1, var_y > 0, var_z_parent > 0)
                disjuncts.append(disj)
            self.solver.assert_and_track(Or(*disjuncts), "{}_span".format(sb))

    def ask(self):
        acc = self._query.acc
        if len(acc) == 1:
            for sb in acc:
                flow = acc[sb] * self.var_x_dict[sb]
                break
        else:
            flow = reduce(lambda a, b: acc[a] * self.var_x_dict[a] + acc[b] * self.var_x_dict[b], acc)
        
        op = self._query.op
        if op == "==":
            self.solver.assert_and_track(flow == self._query.value, "query")
        elif op == "!=":
            self.solver.assert_and_track(flow != self._query.value, "query")
        elif op == ">":
            self.solver.assert_and_track(flow > self._query.value, "query")
        elif op == "<":
            self.solver.assert_and_track(flow < self._query.value, "query")
        elif op == ">=":
            self.solver.assert_and_track(flow >= self._query.value, "query")
        elif op == "<=":
            self.solver.assert_and_track(flow <= self._query.value, "query")

    def check(self):
        self.solver.set(unsat_core=True)
        self.add_basics()
        self.add_flow()
        self.add_connectivity()
        self.ask()
        
        self.result = self.solver.check()
        return self.result

    def get_assertions(self):
        return self.solver.assertions()

    def get_model(self):
        try:
            m = self.solver.model()
            return sorted([(d, m[d]) for d in m], key = lambda x: str(x[0]))
        except Exception as e:
            print(e)

    def get_unsat_core(self):
        return self.solver.unsat_core()
    