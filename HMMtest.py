import sys
from HMM import HMM

if __name__ == "__main__":
    #readings = [0, 2, 1, 0, 1, 3, 2] # Expect 7 for maze.maz
    #rlocs = [8, 9, 10, 6, 2, 3, 7]
    readings = [0, 2, 1, 3] # Expect 11 for maze.maz
    rlocs = [8, 9, 10, 11]
    try:
        import termcolor
        #hmmtest = HMM("walls.maz", coloring = True)
        hmmtest = HMM("maze.maz", coloring = True)
        result = hmmtest.filter(readings, rlocs)

    except Exception as e:
        print(e)
        print("This program relies on the termcolor module for colored text display.")
        print("Install via 'pip install termcolor' or continue with no color")
        nocolor = input("Continue with no color? (y/n) ")
        if 'y' in nocolor:
            #hmmtest = HMM("walls.maz", coloring = False)
            hmmtest = HMM("maze.maz", coloring = False)
            result = hmmtest.filter(readings, rlocs)
        else:
            sys.exit()

    prob = "%.3f" % result[0][0]
    print("Predicted location " + str(result[1]) + " with probability " + str(prob))
    print("Expected: " + str(rlocs[-1]))
