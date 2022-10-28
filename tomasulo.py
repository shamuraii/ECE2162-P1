import units

def main():
    print("ECE 2162 - Project 1","Jefferson Boothe","James Bickerstaff","--------------------",sep="\n")

    print("Loading input file...")
    f = open('instructions.txt', 'r')
    inst_lines = f.readlines()
    inst_lines = [s.lower().strip() for s in inst_lines]

    #int adder, #rs, ex, mem, #fu
    line = inst_lines[0].split(',')
    args = [eval(i) for i in line]
    intA = units.IntAdder(args[1],args[2],args[4])
    #fp adder, #rs, ex, mem, #fu
    line = inst_lines[1].split(',')
    #fp multiplier, #rs, ex, mem, #fu
    line = inst_lines[2].split(',')
    #load/store unit, #rs, ex, mem, #fu
    line = inst_lines[3].split(',')

    line = inst_lines[5].split(',')
    #rob,#entries
    line = inst_lines[6].split(',')
    #cdb,#entries
    line = inst_lines[7].split(',')
    #HARD TO PARSE, REGISTER=VALUE

    #lines 9+ are instructions

    for line in inst_lines:
        print(line)
    print("--------------------")

if __name__ == '__main__':
    main()