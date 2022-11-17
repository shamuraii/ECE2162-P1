
class RegisterAliasTable:
	#using a dict here for unique-ness, can't have 2 R10s for instance
	entries = {}
	copies = []
	numIntegers = 0
	numFloatingPoints = 0
	def __init__(self, intNum, floatNum) -> None:
		self.numIntegers = intNum
		self.numFloatingPoints = floatNum
		#loop through the number of int register entries & initialize RAT for that amount
		for i in range(intNum):
			self.entries['R'+str(i)] = 'R'+str(i)
		#do the same for float regs
		for i in range(floatNum):
			self.entries['F'+str(i)] = 'F'+str(i)

	#method to update RAT entry with new register alias
	def update(self, register, newAlias):
		#first check for valid register
		if register in self.entries:
			#update the register value
			print("RAT UPDATE: ", register, "->", newAlias)
			self.entries[register] = newAlias
		else:
			raise Exception("REGISTER " + register + " INVALID - CANNOT UPDATE RAT")
			
	def clearEntry(self, alias, PC):
		savedName = None
		# If the alias is present in table, clear it
		#print("trying to clear alias ", alias)
		for key,value in self.entries.items():
			if value == alias:
				self.entries[key] = key
				savedName = key
		
		found = False
		#also need to look through RAT copies for the nearest copy made with a higher PC
		#search through list to find dictionary with matching PC
		for dict in self.copies: #grab each dict
			for key,value in dict.items():
				for key2,value2 in value.items():
					#print("Key = ", key, " key2 = ", key2)
					#print("PC = ", PC, " key > PC? ", key > PC)
					#print("Value = ", value2, " alias = ", alias, " equal? ", value2 == alias)
					if value2 == alias:
						if key > PC:
							#found desired PC, modify the entry in the saved checkpoint
							#print("Changing ", dict.get(key)[key2], " to ", key2)
							dict.get(key)[key2] = key2
							#print("dict.get(key)[key2] = ", dict.get(key)[key2])
							found = True
							break
				if found == True:
					break 
			if found == True:
				break
					

	#method to lookup registers
	def lookup(self, register):
		#assuming register found in RAT, return its alias 
		if register in self.entries:
			return self.entries[register]
		else:
			raise Exception("RAT lookup does not exist: " + str(register))
			
	#method to create a copy of the RAT for branch purposes
	def createCopy(self, PC):
		self.copies.append({PC:self.entries.copy()}) #make it so that the saved RAT is correlated to the branch's PC
		return len(self.copies)-1 #return index of this copy
		
	#method to recover RAT in the event of a misprediction
	def recoverRAT(self, PC):
		#using this var to grab the location in the copies array that needs deletion and those that follow - doing outside the loop for reasons
		deletionLocation = None
		#list containing which RS stations related to incorrect branches will need to be cleared, may have multiple chaining branches that need cleared
		entriesToClear = []
		#using a bool for noting when deletion entry is found
		entryFound = False
		#search through list to find dictionary with matching PC
		for dict in self.copies: #grab each dict
			for key in dict.keys(): #grab keys, should only be one since its {key : {other dict}}
				if key == PC:
					self.entries = dict.get(key).copy() #copy dict from copies into the actual entries slot
					#also need to clear any entries that come after this recovered one as they are now stale, so save this index
					deletionLocation = self.copies.index(dict)
					entryFound = True
				if entryFound == True:
					#add this value to the RS entries to clear variable
					entriesToClear.append(self.copies.index(dict))
		#now delete the appropriate entries
		del self.copies[deletionLocation:]
		#return the list of entries that need clearing
		return entriesToClear
					
	#method to clear a RAT copy once branch is resolved and prediction was correct
	def clearCopy(self, PC):
		#search through list to find dictionary with matching PC
		for dict in self.copies: #grab each dict
			for key in dict.keys(): #grab keys, should only be one since its {key : {other dict}}
				if key == PC:
					self.entries.pop(self.copies.index(dict)) #pop this entry to remove
					
		
			
	#print all copies of the RAT for debug
	def printCopies(self):
		for entry in self.copies:
			print(entry)
			
			
	def print(self):
		for key, value in self.entries.items():
			print(str(key), " : ", str(value))
			
	#print machine dont work    
	#print all registers and their aliases
	def __str__(self):
		#print all int reg aliases
		return '\n'.join([str(key, ' : ', value) for key, value in self.entries.items()])

class Instruction:
	def __init__(self, type, field1, field2, field3, PC):
		self.type = type
		self.field1 = field1
		self.field2 = field2
		self.field3 = field3
		self.isCycle = "X"
		self.exCycle = ("X", "X") # (start,end) tuple
		self.memCycle = ("X", "X") # (start,end) tuple
		self.wbCycle = "X"
		self.comCycle = ("X", "X") #need start and end for stores 
		self.PC = PC #adding the PC of an instr for ease of resolving/committing branches later
		self.branchEntry = None #using this for when the instr will need to be cleared from RS if branch is mispredicted

	def copy(self):
		outInstr = Instruction(self.type, self.field1, self.field2, self.field3, self.PC)
		outInstr.setIsCycle(self.isCycle)
		outInstr.setExStart(self.exCycle[0])
		outInstr.setExEnd(self.exCycle[1])
		outInstr.setMemStart(self.memCycle[0])
		outInstr.setMemEnd(self.memCycle[1])
		outInstr.setWbCycle(self.wbCycle)
		outInstr.setComStart(self.comCycle[0])
		outInstr.setComEnd(self.comCycle[1])
		outInstr.setBranchEntry(self.branchEntry)
		return outInstr
	 
	#getters for each part of the instruction
	def getType(self):
		return self.type
		
	def getField1(self):
		return self.field1 #destination

	def getField2(self):
		return self.field2

	def getField3(self):
		return self.field3
		
	def getPC(self):
		return self.PC
		
	def getBranchEntry(self):
		return self.branchEntry
		
	def getExEndCycle(self):
		return self.exCycle[1]
		
	def getIsCycle(self):
		return self.isCycle

	def setIsCycle(self, val):
		self.isCycle = val

	def setExStart(self, val):
		temp = list(self.exCycle)
		temp[0] = val
		self.exCycle = tuple(temp)

	def setExEnd(self, val):
		temp = list(self.exCycle)
		temp[1] = val
		self.exCycle = tuple(temp)

	def setMemStart(self, val):
		temp = list(self.memCycle)
		temp[0] = val
		self.memCycle = tuple(temp)

	def setMemEnd(self, val):
		temp = list(self.memCycle)
		temp[1] = val
		self.memCycle = tuple(temp)

	def setWbCycle(self, val):
		self.wbCycle = val

	def setComStart(self, val):
		temp = list(self.comCycle)
		temp[0] = val
		self.comCycle = tuple(temp)
		
	def setComEnd(self, val):
		temp = list(self.comCycle)
		temp[1] = val
		self.comCycle = tuple(temp)
		
	def setBranchEntry(self, val):
		self.branchEntry = val

	#print statement for instruction
	def __str__(self) -> str:
		if self.type != "NOP" and self.type != "SD" and self.type != "LD": 
			return self.type +' '+ str(self.field1) +','+ str(self.field2) +','+ str(self.field3)
		elif self.type == "SD" or self.type == "LD":
			return self.type +' '+ str(self.field1) +','+ str(self.field2) +'('+ str(self.field3) + ')'
		else:
			return self.type

	def longStr(self):
		return "\t".join([str(self), str(self.isCycle), str(self.exCycle[0]) + "-" + str(self.exCycle[1]), str(self.memCycle[0]) + "-" + str(self.memCycle[1]), str(self.wbCycle), str(self.comCycle[0]) + "-" + str(self.comCycle[1])])

class InstructionBuffer:
	def __init__(self, length) -> None:
		#can use a list as a queue with append and pop(index) if we would like
		self.buffer = [] #list of instrs
		self.length = length
				
	#method to add an instruction directly, adds to the end of buffer
	def addInstr(self, instr, speculatedEntry):
		instr.setBranchEntry(speculatedEntry)
		self.buffer.append(instr)

	#method to empty a buffer entry for later reuse
	def popInstr(self):
		#remove first element (oldest)
		self.buffer.pop(0)
		
	#method to remove specific instructions from the buffer - for use with branches
	def removeInstrs(self, index):
		del self.buffer[index:] #remove from index to end of list
		
	#method to check if there are entries in the instr
	def isEmpty(self):
		return len(self.buffer) == 0

	def isFull(self):
		return len(self.buffer) == self.length
		
	def getNext(self) -> Instruction:
		if self.isEmpty():
			return None
		else:
			#provide first element
			return self.buffer[0]

	#method to print contents of buffer
	def __str__(self):
		#concat all instruction strings
		return '\n'.join(str(entry) for entry in self.buffer)

class ReservationStationEntry:
	def __init__(self) -> None:
		self.busy = 0 #0 = not busy/not in use, 1 = busy/in use
		self.op = "None" #will hold the instruction type
		self.dest = "None" #destination for writeback
		self.value1 = 0 #value of reg/arg 1
		self.value2 = 0 #value of reg/arg 2
		self.dep1 = "None" #holds physical register of dependency 1 - corresponds to value 1
		self.dep2 = "None" #holds physical register of dependency 2 - corresponds to value 2
		self.addr = None #holds address for load/store instructions
		self.cycle = 0 #holds cycle issued to ensure we do not issue and begin execution on same cycle 
		self.instr = None #references the actual Instruction object this entry represents (For saving timing purposes only)
		self.done = 0 #signals that it already executed (could be waiting for CDB to writeback)
		self.branchEntry = None #branch that speculated the instruction this reservation station is holding
		#adding these for the Load/Store queue
		self.offset = None #going to just make a variable for this for ease of access
		self.result = None #value to store or value loaded from memory 
		self.ROBEntry = None #using the ROB entry to clear the queue entry when ready
		self.LDorSDDone = None #using this because LD and SD act differently than regular RS

	def __str__(self):
		return "\t".join(str(i) for i in [self.op, self.dest, self.value1, self.value2, self.dep1, self.dep2, self.addr])

	#returns if this given RS is busy or not
	def checkBusy(self):
		return self.busy
		
	#clears all fields of the RS for reuse
	def clearEntry(self):
		self.busy = 0 
		self.op = "None" 
		self.dest = "None"
		self.value1 = 0 
		self.value2 = 0 
		self.dep1 = "None" 
		self.dep2 = "None" 
		self.addr = 0
		self.cycle = 0
		self.instr = None
		self.done = 0

	#returns dependencies of the RS
	def fetchDep1(self):
		return self.dep1
	def fetchDep2(self):
		return self.dep2

	#method returns True if dependencies do not exist AND not already executed, or False if dependencies do exist 
	def canExecute(self, currCycle):
		return self.op != "None" and self.fetchDep1() == "None" and self.fetchDep2() == "None" and currCycle > self.cycle and self.done == 0
		
	#method returns true if we can calculate the address for a LD or SD
	def canCalcAddress(self, currCycle):
		return self.op != "None" and self.fetchDep2() == "None" and currCycle > self.cycle and self.done == 0
		
	#slight deviation to check if we can begin processing a load or store
	def LDorSDReady(self, currCycle):
		return self.op != "None" and self.fetchDep1() == "None" and self.fetchDep2() == "None" and currCycle > self.cycle 	
			
	#methods to return fields w/ values for computation
	def fetchValue1(self):
		return self.value1
	def fetchValue2(self):
		return self.value2
		
	#method to fetch op to ensure what's going on
	def fetchOp(self):
		return self.op            

	def fetchDest(self):
		return self.dest

	#method to fetch what cycle this instruction was issued on
	def fetchCycle(self):
		return self.cycle

	def fetchInstr(self) -> Instruction:
		return self.instr
		
	#a debug method
	def fetchDone(self):
		return self.done
				
	def fetchBranchEntry(self):
		return self.branchEntry
		
	def fetchAddr(self):
		return self.addr
		
	def fetchOffset(self):
		return self.offset
		
	def fetchResult(self):
		return self.result
		
	def fetchROBEntry(self):
		return self.ROBEntry
		
	def fetchLDorSDDone(self):
		return self.LDorSDDone

	#creating update methods for each because we do not know what will be set initially
	#may have 1 value & 1 dep, 0 value & 2 dep, just an address, etc 

	def updateBusy(self, newBusy):
		self.busy = newBusy

	def updateOp(self, newOp):
		self.op = newOp
		
	def updateDest(self, newDest):
		self.dest = newDest

	def updateValue1(self, newValue1):
		self.value1 = newValue1

	def updateValue2(self, newValue2):
		self.value2 = newValue2
		
	def updateDep1(self, newDep1):
		self.dep1 = newDep1

	def updateDep2(self, newDep2):
		self.dep2 = newDep2
		
	def updateAddr(self, newAddr):
		self.addr = newAddr
		
	def updateCycle(self, newCycle):
		self.cycle = newCycle

	def updateInstr(self, newInstr):
		self.instr = newInstr
				
	def updateBranchEntry(self, newBranchEntry):
		self.branchEntry = newBranchEntry
		
	def updateOffset(self, newOffset):
		self.offset = newOffset
		
	def updateResult(self, newResult):
		self.result = newResult
		
	def updateROBEntry(self, newEntry):
		self.ROBEntry = newEntry

	def markLDorSDDone(self):
		self.LDorSDDone = 1

	def markDone(self):
		self.done = 1

class ROBEntry:
	def __init__(self, op, dest, instr):
		self.op = op
		self.dest = dest
		self.robDest = None #keeping both robDest and dest to know both the original reg as well as the renamed version - helps resolving names in RAT
		self.value = None
		self.done = 0
		self.doneCycle = 0 
		self.instr = instr #references the actual Instruction object this entry represents (For saving timing purposes only)

	def __str__(self) -> str:
		return "\t".join([str(self.op), str(self.dest), str(self.value), str(self.done)])

	def updateValue(self, newValue, cycle):
		#print("Updating ROB entry ", self.robDest, " as complete")
		if self.done: raise Exception("Attempting to update a ROB value that is already completed: ", ",".join([self.op, self.dest, self.value]))
		# Update value and mark as done
		self.value = newValue
		self.done = 1
		self.doneCycle = cycle
		
	def updateStoreValue(self, cycle):
		#print("Updating ROB entry ", self.robDest, " as complete")
		if self.done: raise Exception("Attempting to update a ROB value that is already completed: ", ",".join([self.op, self.dest, self.value]))
		# Update value and mark as done
		#self.value = newValue
		self.done = 1
		self.doneCycle = cycle

	def updateInstr(self, newInstr):
		self.instr = newInstr

	def getOp(self):
		return self.op

	def getDest(self):
		return self.dest

	def getValue(self):
		return self.value

	def getDone(self):
		return self.done

	def getDoneCycle(self):
		return self.doneCycle

	def getInstr(self) -> Instruction:
		return self.instr
		
	def getRobDest(self):
		return self.robDest
		
	#using this to update the destination of the ROBEntry to the "ROBX" counterpart instead of "RX" since there are alias clearing issues otherwise
	def updateRobDest(self, newName):
		self.robDest = newName
		


class ReorderBuffer:
	def __init__(self, length: int) -> None:
		self.length = length
		self.entries = [None] * length
		self.head = 0
		self.tail = 0
		
	def __str__(self):
		return '\n'.join(str(entry) for entry in self.entries[self.tail:self.head])

	def isEmpty(self) -> bool:
		# If oldest instruction is None, all are None
		return self.entries[self.tail] == None

	def isFull(self) -> bool:
		# head=tail means empty or full, if head is a valid entry, then full
		return (self.head == self.tail and self.entries[self.head] != None)
		
	def getTail(self):
		return self.tail
		
	def getHead(self):
		return self.head

	def addEntry(self, op, dest, instr) -> str:
		# Shouldn't occur, Check ROB before adding. This functionality could be changed though
		if self.isFull(): raise Exception("Attempting to add entry to FULL ROB: ", ",".join([op, dest, instr]))
		# Add new entry at head and increment head
		self.entries[self.head] = ROBEntry(op, dest, instr)
		outstr = "ROB" + str(self.head)
		#update the destination with the ROB version of the register 
		self.entries[self.head].updateRobDest(outstr)
		self.head = (self.head + 1) % self.length
		# return "ROB#" where entry was added
		return outstr

	def canCommit(self, cycle) -> bool:
		# return true if oldest entry exists and finished at least last cycle (cant WB and Commit same cycle)
		if self.isEmpty():
			return False
		else:
			return self.entries[self.tail].getDone() != 0 and self.entries[self.tail].getDoneCycle() < cycle

	def writebackROB(self, cdbDest, cdbValue, doneCycle):
		for idx, entry in enumerate(self.entries):
			if str("ROB"+str(idx)) == cdbDest:
				entry.updateValue(cdbValue, doneCycle)
				
	#using a separate method just for branches to mark as done
	def writebackROBBranch(self, oldestInstr, doneCycle):
		#loop through all ROB entries
		for idx, entry in enumerate(self.entries):
			#search for branch that matches the PC
			if entry != None:
				#print("PC = ", entry.getInstr().getPC(), " compPC = ", PC, " instr.getType() = ", instr.getType(), " entry.getInstr() = ", entry.getInstr().getType())
				if oldestInstr.getPC() == entry.getInstr().getPC() and entry.getDone() != 1: #find the entry of the oldest ROB instr (which is a branch) by its PC
					entry.updateValue(None, doneCycle)
				

	def getOldestEntry(self) -> ROBEntry:
		# Return the oldest instruction (could be None)
		return self.entries[self.tail]

	def deleteOldest(self):
		if self.isEmpty(): raise Exception("Attempting to remove entry from EMPTY ROB!")
		self.entries[self.tail] = None
		self.tail = (self.tail + 1) % self.length
		
	#method to search the ROB and find if a value is ready for use that has not yet been committed
	def searchEntries(self, alias):
		#search through entire ROB
		for entry in self.entries:
			#make sure entry exists
			if entry != None:
				#check if the ROB entry we need is there and has the value ready
				if entry.getRobDest() == alias:
					return entry.getValue()
					
	#method  to clear a given entry, useful in deleting incorrectly predicted instructions
	def clearEntry(self, entry):
		if self.isEmpty(): raise Exception("Attempting to remove entry from EMPTY ROB!")
		self.entries[entry] = None
		self.head = (self.head - 1)#may produce a negative value
		#if head was 0 and became -1, make it become the last index in the list
		if self.head == -1:
			self.head = self.length - 1
					
	#method to clear all ROB entries past a given entry - used for clearing speculated instructions
	def clearSpeculatedEntries(self, ROBEntry):
		tail = self.getTail()
		head = self.getHead()
		#using a Bool to know if we need to check from additional entries in event that the ROB has wrapped around
		#e.g. Tail = index 6, Head = index 2 - possible since it is a circular buffer
		checkStart = True
		
		#clear all entries from ROBEntry to the end
		for entry in self.entries[ROBEntry:]:
			#make sure not empty first, if so, we've reached the end of the populated entries, so quit
			if entry == None:
				checkStart = False
				break
			else:
				self.clearEntry(self.entries.index(entry))
				
		#if we need to go through rest of circular buffer start -> Tail, do so
		if checkStart == True:
			for entry in self.entries[0:tail]:
				#make sure not empty first, if so, we've reached the end of the populated entries, so quit
				if entry == None:
					checkStart = False
					break
				else:
					self.clearEntry(self.entries.index(entry))
					
	#method to make a store ready for completion
	def completeStore(self, robAlias, cycle):
		#search through entire ROB
		for entry in self.entries:
			#make sure entry exists
			if entry != None:
				#check if the ROB entry we need is there 
				if entry.getRobDest() == robAlias:
					entry.updateStoreValue(cycle)


