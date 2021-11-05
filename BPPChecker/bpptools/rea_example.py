import bpptools as bt
import z3

# check reachability
rule0 = bt.Rule('S', ['A'])
rule1 = bt.Rule('A', ['A', 'B'])

rules = [rule0, rule1]
ccfg = bt.CCFG(['S', 'A'], rules)
print(ccfg)
print(ccfg.convert())
query = bt.Query({'B': 1}, "==", 2)


def check_reachability(ccfg, query):
    '''given a CCFG-form BPP, and a query(constraint) of a BPP state, return the answer of reachability problem and the used solver'''
    rc = bt.RChecker(ccfg, query)
    print(rc._ccfg)
    result = rc.check()
    print("result:", result)
    print("Assertions in the solver:\n {}".format(rc.get_assertions()))
    if result == z3.sat:
        print("Returned model:\n {}".format(rc.get_model()))
    elif result == z3.unsat:
        print(rc.get_unsat_core())


if __name__ == "__main__":
    check_reachability(ccfg, query)


