import bpptools as bt
import z3


cl_rule0 = bt.Rule('X', ['Y', 'Z'], 'a')
cl_rule1 = bt.Rule('Y', ['X', 'Y'], 'a')
cl_rule2 = bt.Rule('Z', ['X'], 'b')

cl_rules = [cl_rule0, cl_rule1, cl_rule2]
ccfg = bt.CCFG(['X'], cl_rules)

formula0 = bt.EX("a", bt.Query({'Y': 1, 'Z': 1}, ">=", 2))


def check_bounded_liveness(ccfg, formula, bound_k):
    b = bt.BLChecker(ccfg, formula, bound_k)
    print(ccfg)
    print(b.bpp)
    res = b.check()
    print(res)
    # b.write_assertions()
    print(b.get_assertions())
    print(b.get_model())
    # print(b.get_unsat_core())

if __name__ == "__main__":
    check_bounded_liveness(ccfg, formula0, 3)

    
    