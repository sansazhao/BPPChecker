from bpp_gen import input_gen
import os

f1 = "EG(EX(a, Y + Z >= 2))"
f2 = "EG(Imp(X + Y >= 2, EX(a, Conj(X >= 2, Z >= 1))))"
f3 = "EG(AF(X + Y >= 2))"

var_nums = [20, 50, 100]
rule_nums = [10, 20, 30]
formulas = [f1,f2,f3]


for r_num in rule_nums:
    print("----------------")
    for fml in formulas:
        print(r_num, fml)
        input_gen(100, r_num, fml)
        os.system("python3 run.py -b 10 ./benchmarks/bl_phantom") 

