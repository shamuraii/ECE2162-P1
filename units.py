from architecture import Instruction, RegisterAliasTable, ReservationStationEntry, ReorderBuffer

class IntegerARF:
	registers = {}
	def __init__(self) -> None:
		#effectively add 32 registers
		for i in range(32):
			self.registers['R'+str(i)] = 0
			
	def update(self, register, value):
		#first check for valid register
		if register != "R0" and register in self.registers:
			#update the register value
			self.registers[register] = value
		elif register == "R0":
			print("CANNOT UPDATE R0 - HARDWIRED TO 0")
		else:
			print("REGISTER " + register + " INVALID - CANNOT UPDATE ARF")
			
	#method to lookup value corresponding to a register
	def lookup(self, register):
		if register in self.registers:
			return self.registers[register]
			
	def printRows(self):
		index = 1
		line = ""
		for key,value in self.registers.items():
			if value != 0:
				line += (str(key) + " = " + str(value) + " | ")
				index = index + 1
			if index%6 == 0:
				index = 1
				print(line)
				line = ""
		print(line)#must print remaining entries
			
	def __str__(self):
		#stringify all registers and their values
		return '\n'.join([str(key) + '\t' + str(value) for key, value in self.registers.items()])
			
class FloatARF:
	registers = {}
	def __init__(self) -> None:
		#effectively add 32 registers
		for i in range(32):
			self.registers['F'+str(i)] = 0.0
			
	def update(self, register, value):
		#first check for valid register
		if register in self.registers:
			#update the register value
			self.registers[register] = value
		else:
			print("REGISTER " + register + " INVALID - CANNOT UPDATE ARF")
			
	#method to lookup value corresponding to a register
	def lookup(self, register):
		if register in self.registers:
			return self.registers[register]
			
	def printRows(self):
		index = 1
		line = ""
		for key,value in self.registers.items():
			if value != 0:
				line += (str(key) + " = " + str(value) + " | ")
				index = index + 1
			if index%6 == 0:
				index = 1
				print(line)
				line = ""
		print(line) #must print remaining entries
			
	def __str__(self):
		#stringify all registers and their values
		return '\n'.join([str(key) + '\t' + str(value) for key, value in self.registers.items()])

#creating a class for all FUs to inherit from, contains all RS-relevant methods
class unitWithRS:
	#method to check if any available RS's
	def availableRS(self):
		#loop through all RS's
		for entry in self.rs:
			if entry.checkBusy() == 0:
				return self.rs.index(entry) #return first available index in RS
		return -1 #else all RS are found to be busy, return -1 for no RS available

	#method to populate the entry of the RS passed in
	def populateRS(self, entry, op, dest, value1, value2, dep1, dep2, cycle, instr, PC, branchEntry, robAlias):
		#populate fields of chosen RS
		self.rs[entry].updateBusy(1) #mark this RS as now being populated/busy doing computation
		self.rs[entry].updateOp(op) #will hold instruction in use
		self.rs[entry].updateDest(dest)
		self.rs[entry].updateValue1(value1) #will either be a reg. value or placeholder until dep is resolved
		self.rs[entry].updateValue2(value2) #same as line above
		self.rs[entry].updateDep1(dep1) #will be empty or an ROB entry
		self.rs[entry].updateDep2(dep2) #empty or an ROB entry
		self.rs[entry].updateCycle(cycle) #cycle this RS was issued on
		self.rs[entry].updateInstr(instr)
		#self.rs[entry].updatePC(PC) #PC for this instruction
		self.rs[entry].updateBranchEntry(branchEntry)
		self.rs[entry].updateROBEntry(robAlias)
		
	#slight variation of populateRS for the LS Queue since a couple extra vars are needed
	def populateLSQueue(self, entry, op, dest, value1, value2, dep1, dep2, cycle, instr, PC, branchEntry, offset, ROBEntry):
		#populate fields of chosen RS
		self.populateRS(entry, op, dest, value1, value2, dep1, dep2, cycle, instr, PC, branchEntry, ROBEntry)
		#also update the offset, and ROB entry
		self.rs[entry].updateOffset(offset)
		self.rs[entry].updateROBEntry(ROBEntry)
		
	def writebackVals(self, cdbStation, cdbValue):
		cdbDest = cdbStation.fetchDest()
		for entry in self.rs:
			if entry.checkBusy() == 1:
				#check dep 1 for match
				if entry.fetchDep1() == cdbDest:
					entry.updateValue1(cdbValue)
					entry.updateDep1("None")
				#check dep 2 for match
				if entry.fetchDep2() == cdbDest:
					entry.updateValue2(cdbValue) 
					entry.updateDep2("None")  

	def writebackClear(self, cdbStation):
		#clear entry if its the one being WrittenBack
		for entry in self.rs:
			if entry is cdbStation:
				entry.clearEntry()

	#method to check each RS for the requested dependency, returns entry if there is a dependency, or -1 if there is not
	def checkDependencies(self, depCheck):
		#loop through all RS's
		for entry in self.rs:
			#now fetch the dependencies and compare against each
			if entry.fetchDep1() == depCheck:
				return self.rs.index(entry) #return number of entry
			if entry.fetchDep2() == depCheck:
				return self.rs.index(entry) #return number of entry
		#else no dependencies within RS list, return -1
		return -1

	#method to resolve dependencies, probably a better way to do this
	def resolveDep(self, entry, value, dep):
		#first find if it is dependency 1 or 2
		if self.rs[entry].fetchDep1() == dep: #check dep 1 to see if it matches
			self.rs[entry].updateValue1(value) #update to resolved value
			self.rs[entry].updateDep1("None") #clear dependency
		if self.rs[entry].fetchDep2() == dep: #check dep 2 as well to see if it matches
			self.rs[entry].updateValue2(value) #update to resolved value
			self.rs[entry].updateDep2("None") #clear dependency   
		
	#method to grab fields 1 and 2 for computation
	#def fetchArgs(self, entry):
		#return [self.rs[entry].fetchValue1, self.rs[entry].fetchValue2]
		
	#method to clear a RS once it completes
	def clearRS(self, entry):
		self.rs[entry].clearEntry()
		
	#method to check if all RS empty
	def isRSEmpty(self):
		#loop through all RS's
		for entry in self.rs:
			if entry.fetchOp() != "None":
				return False #return false as in all entries are NOT empty
		return True #return true if all empty entries 

	#method to clear RS occupied by mispredicted branch instructions
	def removeSpeculatedInstrs(self, wrongBranches, branchType):
		removed_instr = []
		#loop through entire RS for each deleted branch looking for matches
		#looping through incorrect branches
		for branch in wrongBranches:
			#looping through RS
			for RS in self.rs:
				#not sure if an exception will be thrown for comparing None entries so check that first to short-circuit
				#using last RS.fetchInstr().getType() != branchType check to not accidentally clear out the branch we're executing
				if RS.fetchInstr() != None and RS.fetchBranchEntry() != None and RS.fetchBranchEntry() == branch and RS.fetchInstr().getType() != branchType:
					#if this entry is one that should be cleared, do it
					print("Speculatively Cleared RS for Instr: ", RS.fetchInstr(), "Depth = ", branch)
					removed_instr.append(RS.fetchInstr())
					self.clearRS(self.rs.index(RS))
		return removed_instr
					
					

	def printRS(self):
		for station in self.rs: print(station)

#integer adder is unpipelined - only 1 instr at a time start to finish
class IntAdder(unitWithRS):
	def __init__(self, rs_count: int, ex_cycles: int, fu_count: int) -> None:
		self.rs_count = rs_count
		self.ex_cycles = ex_cycles
		self.fu_count = fu_count
		self.rs = []
		self.currentExe = -1 #-1 if nothing being executed or RS entry if something is in progress
		self.cyclesInProgress = 0 #will keep track of how many cycles this instr has been executing for
		for _ in range(rs_count):
			self.rs.append(ReservationStationEntry())

	#method to add instruction to the reservation stations - will need to add feature for register renaming
	def issueInstruction(self, instr: Instruction, cycle, RAT: RegisterAliasTable, intARF: IntegerARF, robAlias, ROB: ReorderBuffer, PC):
		#find next available RS if there is one - do this first as the rest doesn't matter if no RS available
		nextEntry = self.availableRS()
		if nextEntry == -1:
			# This should be checked BEFORE calling this function
			raise Exception("IntAdder attempting to issue with no available RS")
		#else, nextEntry contains the first available RS entry that will be used
		
		#print("IntAdder RS " +str(nextEntry)+ " new entry: ", instr)
		
		#FIGURE OUT DEPENDENCIES HERE FOR THE REGISTERS IN USE BY CHECKING THE RAT
		dep1 = "None" #RAT.lookup(instr.getField2())
		dep2 = "None"
		value1 = None
		value2 = None
		
		#if it is a traditional add/sub, figure out dependencies and values based on fields 2 and 3
		if instr.getType() == "ADDI":
			# Only 1 dependency, field 3 is immediate, otherwise same as ADD/SUB procedure below
			dep1 = RAT.lookup(instr.getField2())
			RAT.update(instr.getField1(), robAlias)
			dest = RAT.lookup(instr.getField1())
			if dep1 == instr.getField2():
				dep1 = "None"
				value1 = intARF.lookup(instr.getField2())
			# Place immediate value
			dep2 = "None"
			value2 = int(instr.getField3())
			# Check ROB if value is ready immediately
			if ROB.searchEntries(dep1) != None:
				#if the value returned is not None, then a value has been produced and may be used
				value1 = ROB.searchEntries(dep1)
				dep1 = "None"

		elif instr.getType() != "BEQ" and instr.getType() != "BNE":
			#need to grab deps before updating RAT, or else the dependency may be overwritten by the new ROB alias
			dep1 = RAT.lookup(instr.getField2())
			dep2 = RAT.lookup(instr.getField3())
			#dependencies obtained, update RAT
			RAT.update(instr.getField1(), robAlias)
			#and finally set the destination as this instructions ROB entry (could prob just use dest = robAlias here)
			dest = RAT.lookup(instr.getField1())
			#check if the deps are actually just the field names, if so, no deps exist, also must grab values from ARF
			if dep1 == instr.getField2():
				dep1 = "None"
				value1 = intARF.lookup(instr.getField2())
			if dep2 == instr.getField3():
				dep2 = "None"
				value2 = intARF.lookup(instr.getField3())
				
			#also need to check if values are ready immediately within the ROB
			if ROB.searchEntries(dep1) != None:
				#if the value returned is not None, then a value has been produced and may be used
				value1 = ROB.searchEntries(dep1)
				dep1 = "None"
			if ROB.searchEntries(dep2) != None:
				#if the value returned is not None, then a value has been produced and may be used
				value2 = ROB.searchEntries(dep2)
				dep2 = "None"
			
		else: #else, it is a branch, structured as bne/beq Rs, Rt, offset -> comparing Rs to Rt so need to determine deps and values on fields 1 and 2
			#grab dependencies and destination, don't need to worry about register renaming for branches
			dep1 = RAT.lookup(instr.getField1())
			dep2 = RAT.lookup(instr.getField2())
			dest = RAT.lookup(instr.getField1())
			#check if the deps are actually just the field names, if so, no deps exist, also must grab values from ARF
			if dep1 == instr.getField1():
				dep1 = "None"
				value1 = intARF.lookup(instr.getField1())
			if dep2 == instr.getField2():
				dep2 = "None"
				value2 = intARF.lookup(instr.getField2())
				
			#also need to check if values are ready immediately within the ROB
			if ROB.searchEntries(dep1) != None:
				#if the value returned is not None, then a value has been produced and may be used
				value1 = ROB.searchEntries(dep1)
				dep1 = "None"
			if ROB.searchEntries(dep2) != None:
				#if the value returned is not None, then a value has been produced and may be used
				value2 = ROB.searchEntries(dep2)
				dep2 = "None"
				
		
		#now populate the RS with this info - field 2 and field 3 here must be their values, if deps exist they will be overwritten
		self.populateRS(nextEntry, instr.getType(), dest, value1, value2, dep1, dep2, cycle, instr, PC, instr.getBranchEntry(), robAlias)
		print("IntAdder RS ", str(nextEntry), " update: ", self.rs[nextEntry])
			
	#method to fetch next ready instr for execution
	def fetchNext(self, cycle):
		#check if an instruction is already in flight - since no pipelining return if one is in progress
		if self.currentExe != -1:
			return
		#look through reservation stations to find an entry with both fields ready and no dependencies
		#specifically look oldest to newest to ensure an older instruction gets priority to execute
		for entry in sorted(self.rs, key=lambda e: e.fetchCycle()):
			#check for no dependencies and ensure it is not beginning exe on the same cycle it was issued
			if entry.canExecute(cycle):
				#if no deps, execute this one
				print("Executing instr: ", entry.fetchInstr(), " from RS ", self.rs.index(entry), " | ", entry)
				self.currentExe = self.rs.index(entry)
				self.cyclesInProgress = 0 #reset this value, will go 0->ex_cycles
				entry.fetchInstr().setExStart(cycle)
				break
				
				
	#method to execute the next instr chosen
	def exeInstr(self, cycle, CDB, PC, RAT):
		#first check if an instr is actually in flight, if not, just jump out
		if self.currentExe == -1:
			return (None,None)

		#increment the count of cycles in exe stage
		self.cyclesInProgress = self.cyclesInProgress + 1
		#make sure the cycles executed thus far is still < the # it takes
		if self.cyclesInProgress < self.ex_cycles:
			#return, still need to exe for more cycles
			return (None,None)
		
		#else, the cycles in exe have completed, compute the actual result and send it over the CDB to ROB and release RS
		result = None
		curOp = self.rs[self.currentExe].fetchOp()
		if curOp == "ADD" or curOp == "ADDI":
			result = self.rs[self.currentExe].fetchValue1() + self.rs[self.currentExe].fetchValue2()
		elif curOp == "SUB" or curOp == "BEQ" or curOp == "BNE":
			#use subtraction for branch instructions as well, BEQ if Rs - Rt = 0 and BNE if Rs - Rt != 0
			result = self.rs[self.currentExe].fetchValue1() - self.rs[self.currentExe].fetchValue2()
		
		
		#if curOp == "BEQ" or curOp == "BNE":
			#RAT.clearCopy(PC)
		
		print("Result of ", self.rs[self.currentExe].fetchInstr(), " is ", str(result))
		#saving these 3 values now before they are cleared, for branch instruction resolution
		instrPC = self.rs[self.currentExe].fetchInstr().getPC()
		instrField3 = self.rs[self.currentExe].fetchInstr().getField3()
		instrROB = self.rs[self.currentExe].fetchROBEntry()
		#print("instrRob = ", instrROB)
		index = instrROB.split("ROB")
		#print("index = ", index)
		issueCycle = self.rs[self.currentExe].fetchInstr().getIsCycle()
		
		#send to CDB buffer and clear FU, mark RS done
		CDB.newIntAdd(self.rs[self.currentExe], result, cycle)
		self.rs[self.currentExe].fetchInstr().setExEnd(cycle)
		self.rs[self.currentExe].markDone()
		self.currentExe = -1
		self.cyclesInProgress = 0
		
		return (result, instrPC, instrField3, int(index[1]), issueCycle)
		
	#method to grab the instruction currently being executed (if any)
	def clearSpeculativeExe(self, entryToClear):
		#first check if an instr is actually in flight, if not, just jump out
		if self.currentExe == -1:
			return -1
			
		#print("entryToClear = ", entryToClear)
		
		#otherwise, check if the instruction being executed was a recently resolved mispredicted branch, if so, kill it
		if self.rs[self.currentExe].fetchInstr().getBranchEntry() in entryToClear:
			self.currentExe = -1
		
	#method to print the instruction in progress and cycle(s) been in exe stage
	def printExe(self):
		print("-------------------------------------")
		print("INT ADDER EXE INFO")
		print("Reservation station: ", str(self.currentExe))
		print("Instr in progress is: ", str(self.rs[self.currentExe]))
		print("Cycles in progress: ", str(self.cyclesInProgress))
		print("-------------------------------------")
		

	def __str__(self) -> str:
		pass

#float adder is pipelined
class FloatAdder(unitWithRS):
	def __init__(self, rs_count: int, ex_cycles: int, fu_count: int) -> None:
		self.rs_count = rs_count
		self.ex_cycles = ex_cycles
		self.fu_count = fu_count
		self.rs = []
		self.executing = [-1] * rs_count # corresponds to the stage of each RS in execution
		for _ in range(rs_count):
			self.rs.append(ReservationStationEntry())
			
	def issueInstruction(self, instr: Instruction, cycle, RAT: RegisterAliasTable, fpARF: FloatARF, robAlias, ROB: ReorderBuffer, PC):
		# mostly similar to integer adder, only commenting on differences
		nextEntry = self.availableRS()
		if nextEntry == -1:
			raise Exception("FpAdder attempting to issue with no available RS")
		
		# dont need to check type, both add/sub behave the same
		dep1 = RAT.lookup(instr.getField2())
		dep2 = RAT.lookup(instr.getField3())
		value1 = None
		value2 = None
		RAT.update(instr.getField1(), robAlias)
		dest = RAT.lookup(instr.getField1())
		if dep1 == instr.getField2():
			dep1 = "None"
			value1 = fpARF.lookup(instr.getField2())
		if dep2 == instr.getField3():
			dep2 = "None"
			value2 = fpARF.lookup(instr.getField3())

		if ROB.searchEntries(dep1) != None:
			value1 = ROB.searchEntries(dep1)
			dep1 = "None"
		if ROB.searchEntries(dep2) != None:
			value2 = ROB.searchEntries(dep2)
			dep2 = "None"

		self.populateRS(nextEntry, instr.getType(), dest, value1, value2, dep1, dep2, cycle, instr, PC, instr.getBranchEntry(), robAlias)
		print("FpAdder RS ", str(nextEntry), " update: ", self.rs[nextEntry])

	def fetchNext(self, cycle):
		#loop through RS to find an entry ready to execute, prioritize oldest
		for entry in sorted(self.rs, key=lambda e: e.fetchCycle()):
			idx = self.rs.index(entry)
			if self.executing[idx] != -1:
				continue
			elif entry.canExecute(cycle):
				print("Executing instr: ", entry.fetchInstr(), " from RS ", self.rs.index(entry), " | ", entry)
				self.executing[idx] = 0
				entry.fetchInstr().setExStart(cycle)
				break

	def exeInstr(self, cycle, CDB):
		done = False
		for idx, exe in enumerate(self.executing):
			# check if executing
			if exe == -1:
				continue
			self.executing[idx] += 1
			# check if not finished
			if self.executing[idx] < self.ex_cycles:
				continue
			
			# it has finished
			if done:
				raise Exception("Two instructions finished at same time in FpAdder, cycle: " + str(cycle))
			done = True
			result = None
			curOp = self.rs[idx].fetchOp()
			if curOp == "ADD.D":
				result = self.rs[idx].fetchValue1() + self.rs[idx].fetchValue2()
			else:
				result = self.rs[idx].fetchValue1() - self.rs[idx].fetchValue2()
			print("Result of ", self.rs[idx].fetchInstr(), " is ", str(result))

			CDB.newFpAdd(self.rs[idx], result, cycle)
			self.rs[idx].fetchInstr().setExEnd(cycle)
			self.rs[idx].markDone()
			self.executing[idx] = -1

	def clearSpeculativeExe(self, entryToClear):
		for idx, exe in enumerate(self.executing):
			# check if the instr is a recently resolved mispredicted branch
			if self.rs[idx].fetchInstr() != None and self.rs[idx].fetchInstr().getBranchEntry() in entryToClear:
				print("Speculatively Stopped Exe of Instr: ", self.rs[idx].fetchInstr(), "Depth = ", entryToClear)
				self.executing[idx] = -1


class FloatMult(unitWithRS):
	def __init__(self, rs_count: int, ex_cycles: int, fu_count: int) -> None:
		self.rs_count = rs_count
		self.ex_cycles = ex_cycles
		self.fu_count = fu_count
		self.rs = []
		self.executing = [-1] * rs_count # corresponds to the stage of each RS in execution
		for _ in range(rs_count):
			self.rs.append(ReservationStationEntry())        

	def issueInstruction(self, instr: Instruction, cycle, RAT: RegisterAliasTable, fpARF: FloatARF, robAlias, ROB: ReorderBuffer, PC):
		# mostly similar to integer adder, only commenting on differences
		nextEntry = self.availableRS()
		if nextEntry == -1:
			raise Exception("FpMult attempting to issue with no available RS")
		
		# dont need to check type, both add/sub behave the same
		dep1 = RAT.lookup(instr.getField2())
		dep2 = RAT.lookup(instr.getField3())
		value1 = None
		value2 = None
		RAT.update(instr.getField1(), robAlias)
		dest = RAT.lookup(instr.getField1())
		if dep1 == instr.getField2():
			dep1 = "None"
			value1 = fpARF.lookup(instr.getField2())
		if dep2 == instr.getField3():
			dep2 = "None"
			value2 = fpARF.lookup(instr.getField3())

		if ROB.searchEntries(dep1) != None:
			value1 = ROB.searchEntries(dep1)
			dep1 = "None"
		if ROB.searchEntries(dep2) != None:
			value2 = ROB.searchEntries(dep2)
			dep2 = "None"

		self.populateRS(nextEntry, instr.getType(), dest, value1, value2, dep1, dep2, cycle, instr, PC, instr.getBranchEntry(), robAlias)
		print("FpMult RS ", str(nextEntry), " update: ", self.rs[nextEntry])

	def fetchNext(self, cycle):
		#loop through RS to find an entry ready to execute, prioritize oldest
		for entry in sorted(self.rs, key=lambda e: e.fetchCycle()):
			idx = self.rs.index(entry)
			if self.executing[idx] != -1:
				continue
			elif entry.canExecute(cycle):
				print("Executing instr: ", entry.fetchInstr(), " from RS ", self.rs.index(entry), " | ", entry)
				self.executing[idx] = 0
				entry.fetchInstr().setExStart(cycle)
				break

	def exeInstr(self, cycle, CDB):
		done = False
		for idx, exe in enumerate(self.executing):
			# check if executing
			if exe == -1:
				continue
			self.executing[idx] += 1
			# check if not finished
			if self.executing[idx] < self.ex_cycles:
				continue
			
			# it has finished
			if done:
				raise Exception("Two instructions finished at same time in FpMult, cycle: " + str(cycle))
			done = True
			result = None
			curOp = self.rs[idx].fetchOp()
			if curOp == "MULT.D":
				result = float(self.rs[idx].fetchValue1()) * float(self.rs[idx].fetchValue2())
			else:
				raise Exception("FpMult attempting to execute made-up op: " + str(curOp))
			print("Result of ", self.rs[idx].fetchInstr(), " is ", str(result))

			CDB.newFpMult(self.rs[idx], result, cycle)
			self.rs[idx].fetchInstr().setExEnd(cycle)
			self.rs[idx].markDone()
			self.executing[idx] = -1

	def clearSpeculativeExe(self, entryToClear):
		for idx, exe in enumerate(self.executing):
			# check if the instr is a recently resolved mispredicted branch
			if self.rs[idx].fetchInstr() != None and self.rs[idx].fetchInstr().getBranchEntry() in entryToClear:
				self.executing[idx] = -1
				

class MemoryUnit(unitWithRS):
	def __init__(self, rs_count: int, ex_cycles: int, mem_cycles: int, fu_count: int) -> None:
		self.rs_count = rs_count 
		self.ex_cycles = ex_cycles
		self.mem_cycles = mem_cycles
		self.fu_count = fu_count
		self.currentExe = -1 #-1 if nothing being executed or value of queue entry if something is in progress
		self.cyclesInProgress = 0 #will keep track of how many cycles this instr has been executing for
		self.memory = [0] * 64 #256 Bytes -> 64 Words
		self.rs = [] #called rs to make use of the inheritance, but it is actually a FIFO queue
		self.head = 0 #location of the top of the FIFO
		self.tail = 0 #location of the end of the FIFO (next place to fill an entry, not occupied)
		self.currentExe = -1 #-1 if nothing being executed or queue entry if something is in progress
		self.cyclesInProgress = 0 #will keep track of how many cycles this instr has been executing for
		self.currentLDorSD = -1 #similar to currentExe, will be -1 if no LD or SD in progress and the queue entry if one is in progress
		self.MemCyclesInProgress = 0 #similar to cyclesInProgress but for MEM instead of EXE stage
		self.forwardFromStore = False #flag if we are forwarding from a store to a load
		self.indexToForwardFrom = None #index of store we are forwarding data from
		self.storeInProgress = False #flag to note if the operation using memory is a store, if so, we may still perform forward from a store
		self.goingToForward = False #flag for allowing a store to be in progress while attempting forward from store
		self.forwardedLoad = -1 #index of load being forwarded data
		self.forwardedCycles = 0 #cycles of forwarding from data
		for _ in range(rs_count):
			self.rs.append(ReservationStationEntry())
			
	#method to update memory value
	def updateMemory(self, address, newValue):
		#check if address is > 256 which is the limit
		if address > 256:
			print("Trying to update a memory value beyond the 256 Bytes! Value: ", address)
		#also check if memory address is not cleanly divisible by 4, which will cause problems
		temp = address
		if temp % 4 != 0:
			print("The address ", address, " is not cleanly divisible by 4! Incorrect memory may be fetched!")
		#address will be byte addressed e.g. 0,4,8, so divide by 4 for word addressed
		self.memory[int(address/4)] = newValue
		
	#method to grab a requested memory value
	def getMemory(self, address):
		#check if address is > 256 which is the limit
		if address > 256:
			print("Trying to fetch a memory value beyond the 256 Bytes! Value: ", address)
		#also check if memory address is not cleanly divisible by 4, which will cause problems
		temp = address
		if temp % 4 != 0:
			print("The address ", address, " is not cleanly divisible by 4! Incorrect memory may be fetched!")
		#address will be byte addressed e.g. 0,4,8, so divide by 4 for word addressed
		return self.memory[int(address/4)]    

	#method to print the memory values
	def printMemory(self):
		count = 1
		line = ""
		for index in range(64):
			if self.memory[index] != 0:
				line += ("MEM[" + str(index*4) + "] = " + str(self.memory[index]) + " | ")
				count = count + 1
			if count%5 == 0:
				count = 1
				print(line)
				line = ""
		print(line) #must print remaining entries

	#method to check if any available entries in queue
	def nextAvailableEntry(self):
		#check if full, if yes, return -1
		if self.head == self.tail and self.rs[self.head].fetchInstr() != None:
			return -1
		#otherwise, return the next entry to insert an item
		return self.tail

	#method to add an entry to the queue
	#def addEntry(self, PC, dep1, dep2, value1, value2, instr, cycle):
		#self.queue.addEntry(PC, dep1, dep2, value1, value2, instr, cycle)
		
	#method to pop an entry from the queue - ONLY DONE IN FIFO MANNER
	def popEntry(self):
		self.rs.popEntry()  
		
	#method to (try) and issue instructions
	def issueInstruction(self, instr, cycle, RAT, intARF, fpARF, robAlias, ROB, PC):
		#grab the next available entry in the LS Queue
		nextEntry = self.nextAvailableEntry()
		if nextEntry == -1:
			raise Exception("Load/Store Queue attempting to issue with no available entries")
		
		#declare these variables outside the if statements then populate within
		dest = None
		dep1 = "None"
		dep2 = "None"
		value1 = None
		value2 = None
		
		#have different cases for handling dependencies between loads and stores
		if instr.getType() == "LD":
			#if load, looks like this: LD Fa, offset(Ra), where we are loading value at addr offset+Ra into Fa
			#thus, depend upon Ra before we can perform the address computation
			dep1 = "None" #this isn't used for LD
			dep2 = RAT.lookup(instr.getField3()) #this corresponds to the Ra within the instruction
			#now update the RAT with the new destination
			RAT.update(instr.getField1(), robAlias)
			dest = RAT.lookup(instr.getField1())
			#check if we can resolve the dependency (dep2) right away in 2 ways - no need to solve dep1 as it isnt a dependency
			#1. check if the dependency is just the original register name in the ARF
			if dep2 == instr.getField3():
				dep2 = "None"
				value2 = intARF.lookup(instr.getField3())
			#2. check if value exists in ROB but hasn't been committed yet
			if ROB.searchEntries(dep2) != None:
				value2 = ROB.searchEntries(dep2)
				dep2 = "None"
		else:
			#else, it is a store and looks like this: SD Fa, offset(Ra), storing value in Fa to addr offset+Ra
			#thus, depend on both Fa and Ra
			dep1 = RAT.lookup(instr.getField1()) #this dependency is for the value being stored - Fa
			dep2 = RAT.lookup(instr.getField3()) #this corresponds to the Ra within the instruction
			dest = robAlias 
			#no need to update RAT for the store instruction, nothing is going to be written back
			#check if we can resolve the dependencies right away in 2 ways
			#1. check if the dependency is just the original register name in the ARF
			if dep1 == instr.getField1():
				dep1 = "None"
				if "F" in instr.getField1():
					value1 = fpARF.lookup(instr.getField1())
				elif "R" in instr.getField1():
					value1 = intARF.lookup(instr.getField1())
			if dep2 == instr.getField3():
				dep2 = "None"
				value2 = intARF.lookup(instr.getField3())
			#2. check if value exists in ROB but hasn't been committed yet
			if ROB.searchEntries(dep1) != None:
				value1 = ROB.searchEntries(dep1)
				dep1 = "None"
			if ROB.searchEntries(dep2) != None:
				value2 = ROB.searchEntries(dep2)
				dep2 = "None"
				
		#finally, add this instruction to the load/store queue
		self.populateLSQueue(self.tail, instr.getType(), dest, value1, value2, dep1, dep2, cycle, instr, PC, instr.getBranchEntry(), instr.getField2(), robAlias)
		#increment tail 
		self.tail = self.tail + 1

	#method to fetch next ready instr for execution
	#NOTE: I think the addresses may be calculated out of order, but the actual fetching/storing of memory must be carefully ordered
	def fetchNext(self, cycle):
		#check if an instruction is already in flight - since no pipelining then we return if one is in progress
		if self.currentExe != -1:
			return
		#look through the queue to find an entry without any dependencies, and both values ready
		#look from head of queue to tail of queue to traverse the list in order of issue
		for index in range(self.head,self.tail):
			#grab the entry for this index
			entry = self.rs[index]

			#if the instruction has no dependencies, and has not already been completed, send it off to calculate the address in the exe stage
			if entry.canCalcAddress(cycle) and entry.fetchDone() != 1:
				#if no deps, execute this one
				#print("Executing instr: ", entry.fetchInstr(), " from Queue index ", self.rs.index(entry), " | ", entry)
				self.currentExe = self.rs.index(entry)
				self.cyclesInProgress = 0 #reset this value, will go 0->ex_cycles
				entry.fetchInstr().setExStart(cycle)
				break


	#method to execute the next instr in the queue (if ready)
	def exeInstr(self, cycle):
		#first check if an instr is actually in flight, if not, just jump out
		if self.currentExe == -1:
			return 

		#increment the count of cycles in exe stage
		self.cyclesInProgress = self.cyclesInProgress + 1
		#make sure the cycles executed thus far is still < the # it takes
		if self.cyclesInProgress < self.ex_cycles:
			#return, still need to exe for more cycles
			return 
		
		#else, the cycles in exe have completed, compute the actual result, which is the address to LD or SD from
		address = int(self.rs[self.currentExe].fetchOffset()) + int(self.rs[self.currentExe].fetchValue2())    
		#place this resulting address within the queue entry
		self.rs[self.currentExe].updateAddr(address)		
		
		#print result for fun
		print("Address calculation for ", self.rs[self.currentExe].fetchInstr(), " is ", str(address))
		
		#just mark the end of the exe cycle for this instruction, nothing to do for bcast on CDB and instruction is not actually finished
		#LD will finish in MEM stage, then can WB
		#SD will skip MEM and finish in COMMIT stage, doesn't mess with WB
		self.rs[self.currentExe].fetchInstr().setExEnd(cycle)
		self.rs[self.currentExe].markDone()
		self.currentExe = -1
		self.cyclesInProgress = 0
		
		return 
		
	#method to take the earliest ready LD or SD instruction (if there is one) and send it off for actual processing
	def startLDorSD(self, cycle, ROB):
		#if something is already in progress, don't go through this
		#checking if a load or store is in progress as well as if it is NOT a store, we will want to attempt forward from store whenever possible
		if self.currentLDorSD != -1 and self.storeInProgress == False and self.forwardFromStore == False:
			return
			
		#list for keeping track of stores that are yet to be executed, used in checking if loads can proceed or not
		storesList = []	
			
		#search through queue from head to tail
		for index in range(self.head, self.tail):
					
			#if a store, add it to the list
			if self.rs[index].fetchOp() == "SD":
				storesList.append(self.rs[index])
			#print("looking at ", self.rs[index], " LDorSDReady = ", self.rs[index].LDorSDReady(cycle))
			#print("self.rs[index] = ", self.rs[index])
			#print("self.rs[index].fetchLDorSDDone() = ", self.rs[index].fetchLDorSDDone())
			#check if this instruction has no remaining dependencies and is "ready" to be processed , and ensure it has not already been done
			if self.rs[index].LDorSDReady(cycle) == True and self.rs[index].fetchLDorSDDone() == None: 
				#if so, no dependencies exist, but check if the address has been computed
				if self.rs[index].fetchAddr() != None:				
					#address is known, this instruction/RS is ready to process, but must check for a store if it is at the top of the ROB
					if self.rs[index].fetchOp() == "SD" and ROB.getOldestEntry().getRobDest() == self.rs[index].fetchROBEntry() and self.storeInProgress == False:
						#set this instruction to the one in execution and reset cycles variable
						self.currentLDorSD = index
						self.MemCyclesInProgress = 0
						self.storeInProgress = True
						#also set the COM start cycle
						#self.rs[self.currentLDorSD].fetchInstr().setComStart(cycle)
						break
					elif self.rs[index].fetchOp() == "LD" and self.forwardFromStore == False: #else, check if it is a load
						skipLoad = False
						forwardData = False
						#check if stores before it are for the same addr, and if they have their value
						#if a store comes before and points to the same memory address, but does not have its value, do NOT proceed with this load
						#we will fetch a stale value from the memory if that happens
						for item in reversed(storesList):
							#check address and value of the store
							if item.fetchAddr() == self.rs[index].fetchAddr() and item.fetchValue1() == None:
								#if addresses match and value unknown, proceed to check next LD or SD in the queue
								skipLoad = True
								break
							elif item.fetchAddr() == self.rs[index].fetchAddr() and item.fetchValue1() != None:
								forwardData = True
								self.goingToForward = True
								break
						
						
						if skipLoad == False and (self.storeInProgress == False or forwardData == True):
							#need to have 2 cases for setting variables- one where we are forwarding data and one where we load normally
							if self.goingToForward == True:
								self.forwardedLoad = index
								self.forwardedCycles = 0
							else:
								#set this instruction to the one in execution and reset cycles variable
								self.currentLDorSD = index
								self.MemCyclesInProgress = 0
							
							#self.rs[self.currentLDorSD].fetchInstr().setMemStart(cycle)
							break
					#else, it is a store that is not at the top of the ROB and thus cannot be committed yet	
				else:
					#else, address unknown, which is okay for loads as we just wait, but if its a store, back out now
					if self.rs[index].fetchOp() == "SD":
						break
			else:
				#else, check if the address is known and if it is a store, if address NOT known and it IS a store, back out now
				if self.rs[index].fetchAddr() == None and self.rs[index].fetchOp() == "SD":
					break

	#now things get a little tricky
	#method to find the next LD or SD to execute
	#need to traverse list head to tail
		#make a flag for if we see a store or not
			#if store seen, mark it true
			#if this store just seen IS NOT READY to execute, but address IS KNOWN, check the following instructions
				#if a store comes after it, and IS READY to execute, go ahead and start up this entry in the queue
				#if a load comes after it, no matter what, just return without sending an instruction to memory
			#if this store just seen IS NOT READY to execute, but address IS NOT KNOWN, return without sending an instruction to memory
	#need to check for Forwarding-from-a-Store again
		#can perform a forward from store even if there is a LD or SD in progress
	def executeLD(self, cycle, CDB):
		#first check if an instr is actually in flight, if not, just jump out
		if self.currentLDorSD == -1 and self.forwardFromStore == False and self.goingToForward == False:
			return 

		#if a store is in progress, jump out
		if self.rs[self.currentLDorSD].fetchOp() == "SD" and self.goingToForward == False:
			return
			
		#if we are attempting to start on the same cycle the addr was calculated, wait another
		if self.currentLDorSD != -1 and self.rs[self.currentLDorSD].fetchInstr().getExEndCycle() >= cycle and self.goingToForward == False:
			return
		elif self.forwardedLoad != -1 and self.rs[self.forwardedLoad].fetchInstr().getExEndCycle() >= cycle and self.goingToForward == True:
			return

		#otherwise, know a load is in progress, so proceed

		#if an instr is in flight, and is just starting execution, first check if load from a store is possible before going to memory
		if (self.MemCyclesInProgress == 0 and self.goingToForward == False) or (self.goingToForward == True and self.forwardedCycles == 0):
			LDorSDvalue = -1
			if self.goingToForward == True:
				LDorSDvalue = self.forwardedLoad
			else:
				LDorSDvalue = self.currentLDorSD
			self.rs[LDorSDvalue].fetchInstr().setMemStart(cycle)
			print("Instruction ", self.rs[LDorSDvalue].fetchInstr(), " is beginning load from memory")
			#if it is a load (should always be here), check if any stores that come before are pointing towards the same memory address and have their value ready
			if self.rs[LDorSDvalue].fetchOp() == "LD" or self.goingToForward == True:
				#must check the list from this LD location up to the head
				for index in range(LDorSDvalue, self.head-1, -1): #subtracting 1 from head to ensure proper bounds
					#do not care if we see any other loads along the way, not doing load-to-load-forwarding
					#check if this index is a store and if the address matches this one
					if self.rs[index].fetchOp() == "SD" and self.rs[index].fetchAddr() == self.rs[LDorSDvalue].fetchAddr() and self.rs[index].fetchValue1() != None:
						#if yes, perform forwarding-from-a-store and grab the value now instead of fetching from memory
						#self.rs[self.currentLDorSD].updateValue1(self.rs[index].fetchValue1())
						self.forwardFromStore = True
						self.indexToForwardFrom = index
						#send to CDB buffer
						#CDB.newMem(self.rs[self.currentLDorSD], self.rs[self.currentLDorSD].fetchValue1(), cycle)
						#mark the RS as done as well 
						#self.rs[self.currentLDorSD].markDone()
						#self.rs[self.currentLDorSD].markLDorSDDone()
						#since forwarding, need to update the MEM cycles as well
						print("Performing forwarding-from-a-store from ", self.rs[index].fetchInstr(), " to ", self.rs[LDorSDvalue].fetchInstr(), ", will take from cycles ", cycle, "-", cycle+1)
						self.forwardedCycles = self.mem_cycles-1
						#self.MemCyclesInProgress = self.mem_cycles-1
						#self.rs[self.currentLDorSD].fetchInstr().setMemStart(cycle)
						#self.rs[self.currentLDorSD].fetchInstr().setMemEnd(cycle+1)
						#NOTE: ASSUMING WE CAN ONLY FORWARD DATA TO ONE ENTRY PER CYCLE, AND ASSUME THAT IT MAY RUN CONCURRENTLY WITH EITHER A LD OR SD INSTRUCTION
						return   
			elif self.rs[LDorSDvalue].fetchOp() == "SD":
				raise Exception("TRYING TO EXECUTE A SD IN THE EXECUTE LD METHOD!")


		if self.forwardFromStore == True:
			#increment the count of cycles in mem stage
			self.forwardedCycles = self.forwardedCycles + 1
		else:
			#increment the count of cycles in exe stage
			self.MemCyclesInProgress = self.MemCyclesInProgress + 1
			
		
		#make sure the cycles executed thus far is still < the # it takes
		if (self.MemCyclesInProgress < self.mem_cycles and self.forwardFromStore == False) or (self.forwardedCycles < self.mem_cycles and self.forwardFromStore == True):
			#return, still need to exe for more cycles
			return 
					
		loadResult = None
					
		#else, the cycles in exe have completed, go ahead and load the data from memory
		if self.forwardFromStore == True:
			self.rs[self.forwardedLoad].updateValue1(self.rs[self.indexToForwardFrom].fetchValue1())
			loadResult = self.rs[self.forwardedLoad].fetchValue1()
			self.forwardFromStore = False
			self.indexToForwardFrom = None
			self.goingToForward = False
			print("Result of ", self.rs[self.forwardedLoad].fetchInstr(), " is ", str(loadResult))
			#send to CDB buffer, mark RS done, update timing info
			CDB.newMem(self.rs[self.forwardedLoad], loadResult, cycle)
			self.rs[self.forwardedLoad].fetchInstr().setMemEnd(cycle)
			self.rs[self.forwardedLoad].markLDorSDDone()
			#self.rs[self.currentLDorSD].markDone()
			self.forwardedLoad = -1
			self.forwardedCycles = 0
		else:
			loadResult = self.getMemory(self.rs[self.currentLDorSD].fetchAddr())	
			print("Result of ", self.rs[self.currentLDorSD].fetchInstr(), " is ", str(loadResult))
			#send to CDB buffer, mark RS done, update timing info
			CDB.newMem(self.rs[self.currentLDorSD], loadResult, cycle)
			self.rs[self.currentLDorSD].fetchInstr().setMemEnd(cycle)
			self.rs[self.currentLDorSD].markLDorSDDone()
			#self.rs[self.currentLDorSD].markDone()
			self.currentLDorSD = -1
			self.MemCyclesInProgress = 0		
		
		return 
		
		
	#method to execute store instructions
	def executeSD(self, cycle, CDB, ROB):
		#first check if an instr is actually in flight, if not, just jump out
		if self.currentLDorSD == -1:
			return 

		#if a store is in progress, jump out
		if self.rs[self.currentLDorSD].fetchOp() == "LD":
			return
			
		#if we are attempting to start on the same cycle the addr was calculated, wait another
		if self.rs[self.currentLDorSD].fetchInstr().getExEndCycle() >= cycle:
			return

		#if starting the store, set the com start cycle
		if self.MemCyclesInProgress == 0:
			self.rs[self.currentLDorSD].fetchInstr().setComStart(cycle)
			print("Instruction ", self.rs[self.currentLDorSD].fetchInstr(), " is beginning commit and store to memory")

		
		#otherwise, know a store is in progress, so proceed
	
		#increment the count of cycles in exe stage
		self.MemCyclesInProgress = self.MemCyclesInProgress + 1
		#make sure the cycles executed thus far is still < the # it takes
		if self.MemCyclesInProgress < self.mem_cycles:
			#return, still need to exe for more cycles
			return 
				
		#else, the cycles in exe have completed, go ahead and load the data from memory
		self.updateMemory(self.rs[self.currentLDorSD].fetchAddr(), self.rs[self.currentLDorSD].fetchValue1())		
		
		print("Stored value: MEM[", self.rs[self.currentLDorSD].fetchAddr(), "] = ", str(self.rs[self.currentLDorSD].fetchValue1()))
		
		#mark RS done and update timing info
		#CDB.newMem(self.rs[self.currentLDorSD], self.rs[self.currentLDorSD].fetchValue1(), cycle)
		ROB.completeStore(self.rs[self.currentLDorSD].fetchROBEntry(), cycle)
		self.rs[self.currentLDorSD].fetchInstr().setComEnd(cycle)
		self.rs[self.currentLDorSD].markLDorSDDone()
		#self.rs[self.currentLDorSD].markDone()
		self.currentLDorSD = -1
		self.MemCyclesInProgress = 0
		self.storeInProgress = False
		
		return 
		
	#method to return if a store is in progress
	def isSDInProgress(self):
		return self.rs[self.currentLDorSD].fetchOp() == "SD"
		
	#method to clear instruction currently being executed in the event that it is incorrectly predicted
	def clearSpeculativeExe(self, entryToClear):
		#first check if an instr is actually in flight in either EXE or MEM/COM, if nothing is in progress, just jump out
		if self.currentExe == -1 and self.currentLDorSD == -1:
			return -1
					
		#otherwise, check if the instruction being executed was a recently resolved mispredicted branch, if so, kill it
		if self.currentExe != -1 and self.rs[self.currentExe].fetchInstr().getBranchEntry() in entryToClear:
			self.currentExe = -1
		#must check both EXE and MEM
		if self.currentLDorSD != -1 and self.rs[self.currentLDorSD].fetchInstr().getBranchEntry() in entryToClear:
			self.currentLDorSD = -1
		#checking if forwarding in progress that is speculative
		if self.forwardedLoad != -1 and self.rs[self.forwardedLoad].fetchInstr().getBranchEntry() in entryToClear:
			self.forwardedLoad = -1
		
		
			
