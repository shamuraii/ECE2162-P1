import units
import architecture

class Instruction:
    def __init__(self, type, field1, field2, field3):
        self.type = type
        self.field1 = field1
        self.field2 = field2
        self.field3 = field3
        
    def print(self):
        if self.type != "NOP" and self.type != "SD" and self.type != "LD": 
            print(self.type +' '+ self.field1 +','+ self.field2 +','+ self.field3)
        elif self.type == "SD" or self.type == "LD":
            print(self.type +' '+ self.field1 +','+ self.field2 +'('+ self.field3 + ')')
        else:
            print(self.type)

def loadInstructions():
    instructions = []
    #open instruction file and read in all lines
    print("Loading Instruction file...")
    inst_file = open('instructions.txt', 'r')
    inst_lines = inst_file.readlines()

    #parse instructions
    for line in inst_lines:    
        #split each word by commas
        parts = line.split(',')
        #have to split the first part again into instr type and field 1
        instrStart = parts[0].split(' ')
        #grab the type of instruction first
        type = instrStart[0].strip()
        #create vars for the 3 fields Rdestination, Rsrc1, Rsrc2
        field1 = None
        field2 = None
        field3 = None
        if type == "NOP": #if NOP, just make all fields NOP
            field1 = "NOP"
            field2 = "NOP"
            field3 = "NOP"
        elif type == "LD" or type == "SD": #if load or store, need to manipulate some more
            field1 = instrStart[1].strip() #grab the first register as normal
            f2and3 = parts[1].split('(') #split the offset(R) term into [offset, R)]
            field2 = f2and3[0].strip() #grab the 'offset' part and load it into field2
            field3 = f2and3[1].replace(')', '').strip() #strip ')' from the R) factor and load into field3
        else:
            field1 = instrStart[1].strip() #grab destination register
            field2 = parts[1].strip() #grab source 1 reg
            field3 = parts[2].strip() #grab source 2 reg
            
        #add instruction once all parts are parsed
        instructions.append(Instruction(type, field1, field2, field3))
        
    return instructions
    
def printInstructions(instructions):
    print("Printing instructions...\n")
    for curr in instructions:
        curr.print()


def main():
    print("ECE 2162 - Project 1","Jefferson Boothe","James Bickerstaff","--------------------",sep="\n")    

    print("Loading configuration file...")
    f = open('config.txt', 'r')
    config_lines = f.readlines()
    config_lines = [s.lower().strip() for s in config_lines]

    #int adder, #rs, ex, mem, #fu
    line = config_lines[0].split(',')
    args = [eval(i) for i in line]
    intA = units.IntAdder(args[1],args[2],args[4])
    #fp adder, #rs, ex, mem, #fu
    line = config_lines[1].split(',')
    #fp multiplier, #rs, ex, mem, #fu
    line = config_lines[2].split(',')
    #load/store unit, #rs, ex, mem, #fu
    line = config_lines[3].split(',')
    #rob,#entries
    line = config_lines[5].split(',')
    #cdb,#entries
    line = config_lines[6].split(',')
    #HARD TO PARSE, REGISTER=VALUE -- still need to assign reg values to start
    line = config_lines[7].split(',')
    f.close()

    #call instruction method to read txt file
    instructions = loadInstructions()
    printInstructions(instructions)
    
    
    print("--------------------")
    

if __name__ == '__main__':
    main()