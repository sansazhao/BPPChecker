import argparse

from bpptools.bpp import checking

def main():
    parser = argparse.ArgumentParser(description='BPPChecker [version {}]'.format("1.0.0") )
    parser.add_argument("file", help="input file")
    parser.add_argument('-b', '--bound', type=int, help="the bound in bounded model checking liveness")
    parser.add_argument('-o', '--out', help="output file for additional information")
   
    args = parser.parse_args()
    source = args.file
    bound = args.bound
    out = args.out
    checking(out, source, bound)

if __name__ == "__main__":
    main()