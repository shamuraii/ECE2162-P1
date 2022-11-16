import units
import architecture
import cdb
import branchPredictor
import sys

#making PC a global for passing/modifying between "main" and "tryIssueInstr"
PC = 0

def loadInstructions(instr_fname):
	instructions = []
	#open instruction file and read in all lines
	print("Loading Instruction file...")
	inst_file = open(instr_fname, 'r')
	inst_lines = inst_file.readlines()

	#var to keep track of what PC of each instr will be
	PC = 0
	#parse instructions
	for line in inst_lines:    
		line = line.upper()

		# Skip lines that are comments (start with #)
		if line.startswith("#"):
			continue

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

#method to load instructions into the buffer from a designated PC onward
def reloadInstructions(instructions, instrBuffer, PC, speculatedEntry, clearIndex):
	#print("Next buffer entry check: ", instrBuffer.getNext())
	#if instrBuffer.getNext().getBranchEntry() == branchEntry and takenOrNotTaken == 1:
	#	print("Changing clearIndex")
	#	clearIndex = 1

	#first clear instruction buffer after the branch instruction (if not final instruction)
	instrBuffer.removeInstrs(clearIndex) #remove all instructions from index 1 of buffer to the end

	#go from new PC until end of instructions list and add them to the buffer
	for instr in instructions[int(PC):]:
		instrBuffer.addInstr(instr, speculatedEntry)   

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
	instructions: architecture.Instruction
	):
	global PC
	#get next instruction
	issued = False
	instr = instrBuffer.getNext()

	# STEP 1: CHECK INSTRUCTION
	if instr is None:
		print("No instruction issued: Next instruction is 'None'")
		return False

	# STEP 2: CHECK ROB
	robFull = ROB.isFull()
	if robFull:
		print("No instruction issued: ROB FULL")
		return False

	# STEP 3: CHECK TYPE, then appropriate RS
	instrType = instr.getType()
	if instrType == "ADD" or instrType == "ADDI" or instrType == "SUB":
		assignedRS = intAdder.availableRS()
		if assignedRS == -1:
			print("No instruction issued: IntAdder RS full")
			return False
		else:
			# STEP 4: RENAMING PROCESS 
			robAlias = ROB.addEntry(instr.getType(), instr.getField1(), instr)
			#need to rename after grabbing dependencies within issueInstruction method, or else trickling dependencies are messed up
			#ie ADD R4,R4,R1 will be correct, but if followed by ADD R4,R4,R2 the dependency will point to this instrs destination and never get forwarded the result
			#RAT.update(instr.getField1(), robAlias) 
			intAdder.issueInstruction(instr, cycle, RAT, intARF, robAlias, ROB, PC)
			issued = True
	elif instrType == "BEQ" or instrType == "BNE":
		#branch instructions are issued into the reservation stations of int ALU
		assignedRS = intAdder.availableRS()
		if assignedRS == -1:
			print("No instruction issued: IntAdder RS full")
			return False
		else:
			#will return ROB alias, but don't actually need it 
			robAlias = ROB.addEntry(instr.getType(), instr.getField1(), instr)
			print("Branch ROB alias: ", robAlias)
			#issue this instruction to the integer adder
			intAdder.issueInstruction(instr, cycle, RAT, intARF, robAlias, ROB, PC)
			issued = True
			#in addition to issuing the branch for execution and resolution, need to predict the next PC
			nextPC = BP.getEntryPC(PC)
			prediction = BP.getEntryBranchPrediction(PC)
			#need to create a copy of the RAT in case the branch is mispredicted - return this index for marking which instrs are associated w/ the branch
			speculatedEntry = RAT.createCopy(PC) 
			
			if prediction == 1: 
				print("Issuing branch, predicting taken...")
			else:
				print("Issuing branch, predicting NOT taken...")
			
			#reload instructions according to how this branch is predicted, may be redundant if they are already loaded
			#if prediction == 1, then predict the branch is taken, so change PC to that of the one in BTB
			if prediction == 1:
				PC = nextPC
				#also must reload instructions based on predicted branch - last two numbers are for if in recovery and if branch taken or not taken
				reloadInstructions(instructions, instrBuffer, PC, speculatedEntry, 1)
				#have to sub one from PC now because the issued branch instruction will mess up the PC by +1
				PC = PC - 1
			#if branch is predicted to be NOT taken, carry on with PC incrementing normally
			else:
				reloadInstructions(instructions, instrBuffer, PC, speculatedEntry, 0)
			#print("InstrBuffer After")
			#print(instrBuffer)    
	elif instrType == "ADD.D" or instrType == "SUB.D":
		assignedRS = fpAdder.availableRS()
		if assignedRS == -1:
			print("No instruction issued: FpAdder RS full")
			return False
		else: 
			robAlias = ROB.addEntry(instr.getType(), instr.getField1(), instr)
			fpAdder.issueInstruction(instr, cycle, RAT, fpARF, robAlias, ROB, PC)
			issued = True
	elif instrType == "MULT.D":
		assignedRS = fpMult.availableRS()
		if assignedRS == -1:
			print("No instruction issued: FpMult RS full")
			return False
		else: 
			robAlias = ROB.addEntry(instr.getType(), instr.getField1(), instr)
			fpMult.issueInstruction(instr, cycle, RAT, fpARF, robAlias, ROB, PC)
			issued = True
	elif instrType == "LD" or instrType == "SD":
		assignedRS = lsUnit.availableRS()
		if assignedRS == -1:
			print("No instruction issued: lsUnit RS full")
			return False
		else: 
			robAlias = ROB.addEntry(instr.getType(), instr.getField1(), instr)
			lsUnit.issueInstruction(instr, cycle, RAT, intARF, fpARF, robAlias, ROB, PC)
			issued = True
	elif instrType == "NOP":
		issued = True
	else:
		print(instrType, " not implemented yet, cannot issue.")
		issued = False #TODO, placeholder/example

	# STEP 5: POP BUFFER, SAVE CYCLE INFO
	if issued:
		instr.setIsCycle(cycle)
		instrBuffer.popInstr()
		print(instr, " issued on cycle: ", cycle)
		
	#returning issued variable to see if we should increment PC
	return issued
			
def checkIfDone(
	instrBuffer: architecture.InstructionBuffer,
	ROB: architecture.ReorderBuffer
	):
	#check if instructions left to issue or commit
	return instrBuffer.isEmpty() and ROB.isEmpty()

def main():
	global PC
	print("ECE 2162 - Project 1","Jefferson Boothe","James Bickerstaff","--------------------",sep="\n")    

	argc = len(sys.argv)
	if argc < 3:
		print("Missing arguments. Usage:\npython tomasulo.py config.txt instructions.txt")
		return
	
	config_fname = sys.argv[1]
	instr_fname = sys.argv[2]
		
	print("Loading configuration file...")
	f = open(config_fname, 'r')
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
	#MUST STILL PARSE MEMORY VALUES *************************
	initMemValues = config_lines[9].split(',')
	for init in initMemValues:
		if init != "":
			#kinda hacky way to do this
			pair = init.split('=')
			value = float(pair[1])
			pair1 = pair[0].split('[')
			pair2 = pair1[1].split(']')
			index = int(pair2[0])
			#update mem value
			lsUnit.updateMemory(index, value)
	#parsing if branch instructions refer to PC in byte (1) or relative format (anything else)
	PCConfig = config_lines[10].split('=')
	PCMode = int(PCConfig[1])
	#print("PCMode = ", PCMode)

		
		
	f.close()

	#call instruction method to read txt file
	instrList = loadInstructions(instr_fname)
	outputList = []
	printInstructions(instrList)
	for entry in instrList:
		instrBuffer.addInstr(entry, None)
	#print(instrBuffer)     
	print("--------------------")

	#print("ROB tail = ", ROB.getTail())
	#print("ROB head = ", ROB.getHead())

	#cycle variable to keep track of cycle number
	cycle = 0
	#Program counter variable to keep track of where we are in the program & to deal with branches
	PC = 0
	#variable to pause Issuing of next instructions in the event of a misprediction, must wait a cycle for correct instrs to be placed within the buffer
	pauseIssue = False
	#variable to see if done processing yet
	isDone = False
	#go until all instructions are complete
	#instruction list feeds into the instruction buffer, has a limited window size
	while isDone == False:
		#begin with printing out the current cycle number
		print("Cycle: " + str(cycle))
		print("PC: " + str(PC))
		
		#print("InstrBuffer")
		#print(instrBuffer)

		#make sure Issuing is not paused due to misprediction, if not, issue next instructions if possible
		if pauseIssue == False:
			#place next instrs available into reservation stations, will also need to rename the registers in this step
			issued = tryIssueInstr(instrBuffer, intAdder, fpAdder, fpMult, lsUnit, cycle, RAT, intARF, fpARF, ROB, BP, instrList)
			#if issued the next instr, increase PC
			if issued == True:
				PC = PC + 1
		else:
			#only need to pause issuing for a cycle, free to resume on the next one
			pauseIssue = False

		#print(ROB)

		#fetch next instrs for the FUs, if possible
		intAdder.fetchNext(cycle)
		fpAdder.fetchNext(cycle)
		fpMult.fetchNext(cycle)
		lsUnit.fetchNext(cycle)
		
		#exe instructions for each FU, if possible - using a return tuple to signify result of a branch (-1 if not done, not branch instr, X otherwise)
		results = intAdder.exeInstr(cycle, CDB)
		fpAdder.exeInstr(cycle, CDB)
		fpMult.exeInstr(cycle, CDB)
		lsUnit.exeInstr(cycle)
		#also look to start a load or store within the MEM or COM stage
		lsUnit.startLDorSD(cycle, ROB)
		lsUnit.executeLD(cycle, CDB)
		lsUnit.executeSD(cycle, CDB, ROB)

		#now check if results has -1s in it or not, tuple goes: (result of calculation, PC of instruction)
		if results[0] != None and results[1] != None:
			#values are not invalid values, check result of the branch
			calculation = results[0]
			branchPC = results[1] 
			offset = results[2]
			#first need whether it is BEQ or BNE
			branchType = instrList[branchPC].getType()
						
			#make sure its a branch here in case something goofy happens down the line with testing
			if branchType == "BEQ" or branchType == "BNE":
				#print("Branch PC = ", branchPC)
				#print("BTB")
				#BP.print()
						
				#now check result accordingly
				#check the BP to see if this branch was predicted to be taken or not (returns expected PC)
				prediction = BP.getEntryBranchPrediction(branchPC)
				#bool holding actual result of the branch
				wasBranchTaken = None
				#bool for if we made the correct prediction 
				misprediction = False
				#check if op is BEQ or BNE first
				if branchType == "BEQ":
					#find if branch is actually taken by looking at result of EXE stage
					wasBranchTaken = (calculation == 0)
				elif branchType == "BNE":
					#find if branch is actually taken by looking at result of EXE stage
					wasBranchTaken = (calculation != 0)    
					
				#need to compare 2 cases: predicted taken and predicted not taken
				if prediction == 1:
					#misprediction is true if we predicted taken and it was NOT taken
					misprediction = (wasBranchTaken == False)
				else:
					#misprediction is true if we predicted NOT taken and it was taken
					misprediction = (wasBranchTaken == True)
				
				#print("prediction = ", prediction)
				#print("misprediction = ", misprediction)
				#print("wasBranchTaken = ", wasBranchTaken)
				
				#case of misprediction - predicted don't take it and branch was supposed to be taken
				if misprediction == True:
					print("Branch mispredicted, recovering...")
					#mispredicted this branch, need to recover:
					#1. recover the rat
					RSEntriesToClear = RAT.recoverRAT(branchPC)
					#print("Recovered RAT")
					#RAT.print()
					
					#2. clear speculative RS entries
					#print("Before")
					#intAdder.printRS()
					intAdder.removeSpeculatedInstrs(RSEntriesToClear, branchType)
					fpAdder.removeSpeculatedInstrs(RSEntriesToClear, branchType)
					fpMult.removeSpeculatedInstrs(RSEntriesToClear, branchType)
					lsUnit.removeSpeculatedInstrs(RSEntriesToClear, branchType)
					#print("After")
					#intAdder.printRS()
					#WILL NEED TO DO THIS FOR ALL OTHER UNITS AND THEIR RESERVATION STATIONS ****************
					
					#3. clear ROB entries following the branch
					ROB.clearSpeculatedEntries(branchPC)
					
					#4. update BTB
					#print("BTB Before")
					#BP.print()
					BP.updateBTB(branchPC, wasBranchTaken, offset, PCMode) 
					#print("BTB after")
					#BP.print()
					
					#5. reset the PC to correct value
					#print("PC before")
					#print(PC)
					PC = BP.getEntryPC(branchPC) #since branch should not have been taken, jump to calculated PC
					#print("PC after")
					#print(PC)
					
					#6. clear any executing speculated instructions from FUs - kill their exe in its tracks
					intAdder.clearSpeculativeExe(RSEntriesToClear)
					fpAdder.clearSpeculativeExe(RSEntriesToClear)
					fpMult.clearSpeculativeExe(RSEntriesToClear)
					lsUnit.clearSpeculativeExe(RSEntriesToClear)
					#WILL NEED TO DO THIS FOR ALL OTHER UNITS ****************
					
					#7. fetch correct instructions
					#print("InstrBuffer Before")
					#print(instrBuffer)
					if wasBranchTaken == True:
						reloadInstructions(instrList, instrBuffer, PC, None, 0) #not passing a speculatedEntry, as this is the correct instr path now
					else:
						reloadInstructions(instrList, instrBuffer, PC, None, 0) #not passing a speculatedEntry, as this is the correct instr path now
					#print("InstrBuffer After")
					#print(instrBuffer)
					#this will take the next cycle to complete, resume fetching on x+2 cycles
					pauseIssue = True
				else:
					#else, branch predicted correctly, take no action
					print("Branch predicted correctly! No need to recover")
		
		#print instruction in execution for FUs - debug
		#intAdder.printExe()
		#intAdder.printRS()
		
		#allow cdb to writeback
		CDB.writeBack(cycle)


		#grabbing these two here to check if a store instr can be committed, think the WB stage throws off timing otherwise by 1 cycle
		entry = ROB.getOldestEntry()
		comInstr = entry.getInstr()
		#allow rob to commit if the top entry is able and a store is not in progress halting the commit stage, or if the entry is a store and is just finishing
		if (ROB.canCommit(cycle) and lsUnit.isSDInProgress() == False) or (entry.getOp() == "SD" and entry.getDone() == 1):
			entry = ROB.getOldestEntry()
			comInstr = entry.getInstr()
			print("ROB Commit: ", comInstr)

			if entry.getOp() != "SD":
				#update commit cycle
				comInstr.setComStart(cycle)
				comInstr.setComEnd(cycle)
			
			#don't update ARF and RAT for branches
			if comInstr.getType() != "BNE" and comInstr.getType() != "BEQ" and comInstr.getType() != "SD":
				# Update ARF
				if 'R' in entry.getDest():
					intARF.update(entry.getDest(), entry.getValue())
				elif 'F' in entry.getDest():
					fpARF.update(entry.getDest(), entry.getValue())
				# Remove from RAT if applicable
				RAT.clearEntry(entry.getRobDest(), comInstr.getPC())
			# Remove from ROB
			ROB.deleteOldest()
			# Add to final output
			outputList.append(comInstr.copy())

		#check if program has issued and committed all instructions
		isDone = checkIfDone(instrBuffer, ROB)
		
		cycle = cycle + 1
		print()

		#DEBUG
		if cycle > 100:
			print("Error: DEBUG max cycles.")
			break

	printInstructionsLong(outputList)
	print()
	intARF.printRows()
	print()
	fpARF.printRows()
	print()
	lsUnit.printMemory()
	print()

if __name__ == '__main__':
	main()