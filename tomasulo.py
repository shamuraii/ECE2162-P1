import units
import architecture

def loadInstructions():
    instructions = []
    #open instruction file and read in all lines
    print("Loading Instruction file...")
    inst_file = open('instructions.txt', 'r')
    inst_lines = inst_file.readlines()

    #parse instructions
    for line in inst_lines:    
        line = line.upper()
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
        instructions.append(architecture.Instruction(type, field1, field2, field3))
        
    return instructions
    
def printInstructions(instructions):
    print("Printing instructions...")
    for inst in instructions: print(inst)

def printInstructionsLong(instructions):
    print("--------------------")
    print("Final Results")
    print("\t".join(["Instruction","IS", "EX", "MEM", "WB", "COM"]))
    for inst in instructions: print(inst.longStr())

def issueInstructions(
    instrBuffer: architecture.InstructionBuffer,
    intAdder: units.IntAdder,
    fpAdder: units.FloatAdder,
    fpMult: units.FloatMult,
    lsUnit: units.MemoryUnit,
    cycle: int,
    RAT: architecture.RegisterAliasTable,
    intARF: units.IntegerARF,
    fpARF: units.FloatARF
):

    #need to look at the operation type and decide which FU to send them off to
    for instr in instrBuffer.getList():
        #look at the type
        #if add, try to add it to the add reservation stations
        if instr.getType() == "ADD" or instr.getType() == "SUB":
            #issue instruction to add/sub unit
            successfulIssue = intAdder.issueInstructions(instr, cycle, RAT, intARF)
            #if true, remove the instr from the buffer, otherwise do not remove since it could not be issued
            if successfulIssue:
                instrBuffer.clearEntry(instrBuffer.getList().index(instr))
                break #only issue one instr per cycle
                
            #NEED TO DECIDE IF REGISTER RENAMING WILL BE DONE HERE OR WITHIN THE "issueInstructions" METHOD
            
def checkIfDone(
    instrBuffer: architecture.InstructionBuffer,
    intAdder: units.IntAdder,
    fpAdder: units.FloatAdder,
    fpMult: units.FloatMult,
    lsUnit: units.MemoryUnit
):
    #check if instrBuffer is empty
    if instrBuffer.isEmpty() == False:
        return False #still instructions left, keep going
    #check RS of each FU as well
    if intAdder.isRSEmpty() == False:
        return False #still entries in RS that need processing, keep going
    #check RS of other units
    #check ROB for entries that need committing
    
    #if everything empty, return true to finish the processing
    return True
    


def main():
    print("ECE 2162 - Project 1","Jefferson Boothe","James Bickerstaff","--------------------",sep="\n")    

    print("Loading configuration file...")
    f = open('config.txt', 'r')
    config_lines = f.readlines()
    config_lines = [s.strip() for s in config_lines]
    
    intARF = units.IntegerARF()
    fpARF = units.FloatARF()
    RAT = architecture.RegisterAliasTable(32, 32) #using 32 and 32, shouldn't have to change as there are 32 int and fp logical regs
    
    #int adder, #rs, ex, mem, #fu
    line = config_lines[0].split(',')
    intAdder = units.IntAdder(int(line[1]),int(line[2]),int(line[4]))
    #fp adder, #rs, ex, mem, #fu
    line = config_lines[1].split(',')
    fpAdder = units.FloatAdder(int(line[1]),int(line[2]),int(line[4]))
    #fp multiplier, #rs, ex, mem, #fu
    line = config_lines[2].split(',')
    fpMult = units.FloatMult(int(line[1]),int(line[2]),int(line[4]))
    #load/store unit, #rs, ex, mem, #fu
    line = config_lines[3].split(',')
    lsUnit = units.MemoryUnit(int(line[1]),int(line[2]),int(line[3]),int(line[4]))
    #instruction buffer, number of entries
    line = config_lines[4].split(',')
    instrBuffer = architecture.InstructionBuffer(int(line[1]))
    #rob,#entries
    line = config_lines[6].split(',')
    #cdb,#entries
    line = config_lines[7].split(',')
    #HARD TO PARSE, REGISTER=VALUE -- still need to assign reg values to start - done
    initValues = config_lines[8].split(',')
    #have a list of [R=V,R=V] entries, parse this
    for init in initValues:
        pair = init.split('=')
        #check if an int reg or FP reg
        if 'R' in pair[0]:
            intARF.update(pair[0].upper(), int(pair[1])) #update value
        else:
            fpARF.update(pair[0], float(pair[1])) #update value
        
    f.close()
    
    #call instruction method to read txt file
    instrList = loadInstructions()
    printInstructions(instrList)
    for entry in instrList:
        instrBuffer.addInstr(entry)
    #instrBuffer.print()     
    print("--------------------")

    #cycle variable to keep track of cycle number
    cycle = 0
    #variable to see if done processing yet
    isDone = False
    #go until all instructions are complete
    #instruction list feeds into the instruction buffer, has a limited window size
    while isDone == False:
        #begin with printing out the current cycle number
        print("Cycle: " + str(cycle))
    
        #place next instrs available into reservation stations, will also need to rename the registers in this step
        issueInstructions(instrBuffer, intAdder, fpAdder, fpMult, lsUnit, cycle, RAT, intARF, fpARF)
    
        #fetch next instrs for the FUs, if possible
        intAdder.fetchNext(cycle)
        
        #exe instructions for each FU, if possible
        intAdder.exeInstr()
        
        #print instruction in execution for FUs - debug
        #intAdder.printExe()
        
        #fill empty instruction buffer slots with new instructions
        
        #print("\nADDER RS")
        #intAdder.printRS()
        #print("\n")
        
        #check if all RS and instruction buffers are empty, if so, exit loop
        #will also need to make sure all instructions have committed through the ROB **********
        isDone = checkIfDone(instrBuffer, intAdder, fpAdder, fpMult, lsUnit)
        
        cycle = cycle + 1
        print()

    print("Finished.")
    printInstructionsLong(instrList)
    

if __name__ == '__main__':
    main()