import os
import time
from decimal import Decimal
from functools import wraps
from z3 import sat, unsat, set_option

from bpptools.parser import get_parse_tree, parse_rea, parse_bl
from bpptools.checker.rchecker import RChecker
from bpptools.checker.blchecker import BLChecker

set_option(max_args=10000000, max_lines=1000000, max_depth=10000000, max_visited=1000000)

def timethis(func):
    '''decorator that reports the execution time'''
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        func(*args, **kwargs)
        end = time.time()
        time_used = Decimal(end - start).quantize(Decimal('0.00000'))
        print("time used: " + str(time_used) + "s")
    return wrapper


@timethis
def checking_rea(out, parse_res):
    rchecker = RChecker(*parse_res)
    check_res = rchecker.check()
    if check_res == sat or check_res == unsat:
        print(check_res)
    else:
        print("z3 can not solve this problem!")
        return

    if out:
        with open(out, 'w+') as f:
            if check_res == sat:
                f.write("Returned model:\n")
                f.write(str(rchecker.get_model()))
            elif check_res == unsat:
                f.write("\nReturned unsat core:\n")
                f.write(str(rchecker.get_unsat_core()))
            else:
                f.write("z3 can not solve this problem!")
            f.write("\n\nAssertions:\n")
            f.write(str(rchecker.get_assertions()))


@timethis
def checking_bl(out, parse_res, bound):
    blchecker = BLChecker(*parse_res, bound)
    check_res = blchecker.check()
    if check_res == sat or check_res == unsat:
        print(check_res)
    else:
        print("z3 can not solve this problem!")
        return
    
    if out:
        with open(out, 'w+') as f:
            if blchecker.non_nested:
                if check_res == sat:
                    f.write("Returned model:\n")
                    f.write(str(blchecker.get_model()))
                elif check_res == unsat:
                    f.write("\nReturned unsat core:\n")
                    f.write(str(blchecker.get_unsat_core()))
                else:
                    f.write("z3 can not solve this problem!")
            f.write("\n\nStats of constraints:\n")
            f.write(str(blchecker.get_cstr_statistics()))
            f.write("\n\nStats from z3:\n")
            f.write(str(blchecker.get_z3_statistics()))
            f.write("\n\nAssertions:\n")
            f.write(str(blchecker.get_assertions()))
        

def checking(out, source: str, bound: int = 0):
    try:
        if os.path.isfile(source):
            with open(source) as file:
                text = file.read()
        else:
            raise Exception(f"File {source} not found")

        parse_tree = get_parse_tree(text)
        problem = parse_tree.children[0]

        if problem.data == "rea":
            parse_res = parse_rea(problem)
            checking_rea(out, parse_res)
        elif problem.data == "bl":
            parse_res = parse_bl(problem)
            # print(parse_res)
            if type(parse_res[1]).__name__ == "Query":
                checking_rea(out, parse_res)
            else:
                checking_bl(out, parse_res, bound)
        else:
            raise SyntaxError("Unknown problem type: {}".format(problem.data))

    except Exception as exception:
        print("Execution failed!")
        print(exception)

