import random


def input_gen(var_num, rule_num, formula):
    with open("./benchmarks/bl_phantom", 'w+') as f:
        f.write("initial\n")
        f.write("X_1\n\n")
        f.write("rules\n")
        
        for index in range(rule_num):
            i = random.randint(1, var_num)
            j = random.randint(1, var_num)
            k = random.randint(1, var_num)
            action = chr(97 + random.randint(0, 1))
            f.write("X_{} -> {} -> X_{}, X_{}\n".format(i, action, j, k))

        f.write("\nformula\n")
        f.write(formula)


