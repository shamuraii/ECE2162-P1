import units
import architecture
import cdb
import branchPredictor

def loadInstructions():
    instructions = []
    #open instruction file and read in all lines
    print("Loading Instruction file...")
    inst_file = open('instructions.txt', 'r')
    inst_lines = inst_file.readlines()

    #var to keep track of what PC of each instr will be
    PC = 0
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
        instructions.append(architecture.Instruction(type, field1, field2, field3, PC))
        PC = PC + 1
        
    return instructions
    
def printInstructions(instructions):
    print("Printing instructions...")
    for inst in instructions: print(inst)

def printInstructionsLong(instructions):
    print("--------------------")
    print("Final Results")
    print("\t".join(["Instruction","IS", "EX", "MEM", "WB", "COM"]))
    for inst in instructions: print(inst.longStr())

def tryIssueInstr(
    instrBuffer: architecture.InstructionBuffer,
    intAdder: units.IntAdder,
    fpAdder: units.FloatAdder,
    fpMult: units.FloatMult,
    lsUnit: units.MemoryUnit,
    cycle: int,
    RAT: architecture.RegisterAliasTable,
    intARF: units.IntegerARF,
    fpARF: units.FloatARF,
    ROB: architecture.ReorderBuffer,
    BP: branchPredictor.BranchPredictor,
    PC: int
):
    #get next instruction
    issued = False
    instr = instrBuffer.getNext()

    # STEP 1: CHECK INSTRUCTION
    if instr is None:
        print("No instruction issued: Next instruction is 'None'")
        return

    # STEP 2: CHECK ROB
    robFull = ROB.isFull()
    if robFull:
        print("No instruction issued: ROB FULL")
        return
    
    # STEP 3: CHECK TYPE, then appropriate RS
    instrType = instr.getType()
    if instrType == "ADD" or instrType == "SUB":
        assignedRS = intAdder.availableRS()
        if assignedRS == -1:
            print("No instruction issued: RS full")
            return
        else:
            # STEP 4: RENAMING PROCESS 
            robAlias = ROB.addEntry(instr.getType(), instr.getField1(), instr)
            #need to rename after grabbing dependencies within issueInstruction method, or else trickling dependencies are messed up
            #ie ADD R4,R4,R1 will be correct, but if followed by ADD R4,R4,R2 the dependency will point to this instrs destination and never get forwarded the result
            #RAT.update(instr.getField1(), robAlias) 
            intAdder.issueInstruction(instr, cycle, RAT, intARF, robAlias, ROB)
            issued = True
    elif instrType == "BEQ" or instrType == "BNE":
        #branch instructions are issued into the reservation stations of int ALU
        assignedRS = intAdder.availableRS()
        if assignedRS == -1:
            print("No instruction issued: RS full")
            return
        else:
            #will return ROB alias, but don't actually need it 
            robAlias = ROB.addEntry(instr.getType(), instr.getField1(), instr)
            #issue this instruction to the integer adder
            intAdder.issueInstruction(instr, cycle, RAT, intARF, robAlias, ROB)
            issued = True
    else:
        issued = False #TODO, placeholder/example
    
    # STEP 5: POP BUFFER, SAVE CYCLE INFO
    if issued:
        instr.setIsCycle(cycle)
        instrBuffer.popInstr()
        print(instr, " issued on cycle: ", cycle)
            
def checkIfDone(
    instrBuffer: architecture.InstructionBuffer,
    ROB: architecture.ReorderBuffer
):
    #check if instructions left to issue or commit
    return instrBuffer.isEmpty() and ROB.isEmpty()
    


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
    ROB = architecture.ReorderBuffer(int(line[1]))
    #cdb,#entries
    line = config_lines[7].split(',')
    CDB = cdb.CommonDataBus(int(line[1]), intAdder, fpAdder, fpMult, lsUnit, ROB)
    #create the branch predictor unit
    BP = branchPredictor.BranchPredictor()
    #parse register values
    initValues = config_lines[8].split(',')
    #have a list of [R=V,R=V] entries, parse this
    for init in initValues:
        pair = init.split('=')
        #check if an int reg or FP reg
        if 'R' in pair[0]:
            intARF.update(pair[0].upper(), int(pair[1])) #update value
        else:
            fpARF.update(pair[0].upper(), float(pair[1])) #update value
        
    f.close()
    
    #call instruction method to read txt file
    instrList = loadInstructions()
    printInstructions(instrList)
    for entry in instrList:
        instrBuffer.addInstr(entry)
    #print(instrBuffer)     
    print("--------------------")

    #cycle variable to keep track of cycle number
    cycle = 0
    #Program counter variable to keep track of where we are in the program & to deal with branches
    PC = 0
    #variable to see if done processing yet
    isDone = False
    #go until all instructions are complete
    #instruction list feeds into the instruction buffer, has a limited window size
    while isDone == False:
        #begin with printing out the current cycle number
        print("Cycle: " + str(cycle))
        print("PC: " + str(PC))
    
        #place next instrs available into reservation stations, will also need to rename the registers in this step
        tryIssueInstr(instrBuffer, intAdder, fpAdder, fpMult, lsUnit, cycle, RAT, intARF, fpARF, ROB, BP, PC)
    
        #fetch next instrs for the FUs, if possible
        intAdder.fetchNext(cycle)
        
        #exe instructions for each FU, if possible
        intAdder.exeInstr(cycle, CDB)
        
        #print instruction in execution for FUs - debug
        #intAdder.printExe()
        #intAdder.printRS()
        
        #allow cdb to writeback
        CDB.writeBack(cycle)

        #allow rob to commit
        if ROB.canCommit(cycle):
            entry = ROB.getOldestEntry()
            print("ROB Commit: ", entry.getInstr())

            #update commit cycle
            entry.getInstr().setComCycle(cycle)
            
            #don't update ARF and RAT for branches
            if entry.getInstr().getType() != "BNE" and entry.getInstr().getType() != "BEQ":
                # Update ARF
                if 'R' in entry.getDest():
                    intARF.update(entry.getDest(), entry.getValue())
                elif 'F' in entry.getDest():
                    fpARF.update(entry.getDest(), entry.getValue())
                # Remove from RAT if applicable
                RAT.clearEntry(entry.getRobDest())
            # Remove from ROB
            ROB.deleteOldest()

        #check if program has issued and committed all instructions
        isDone = checkIfDone(instrBuffer, ROB)
        
        cycle = cycle + 1
        PC = PC + 1
        print()

        #DEBUG
        if cycle > 100:
            print("Error: DEBUG max cycles.")
            break

    printInstructionsLong(instrList)
    print(intARF)
    print(fpARF)

if __name__ == '__main__':
    main()