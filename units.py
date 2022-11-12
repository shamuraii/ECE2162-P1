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
    def populateRS(self, entry, op, dest, value1, value2, dep1, dep2, cycle, instr, PC, branchEntry):
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
        #loop through entire RS for each deleted branch looking for matches
        #looping through incorrect branches
        for branch in wrongBranches:
            #looping through RS
            for RS in self.rs:
                #not sure if an exception will be thrown for comparing None entries so check that first to short-circuit
                #using last RS.fetchInstr().getType() != branchType check to not accidentally clear out the branch we're executing
                if RS.fetchBranchEntry() != None and RS.fetchBranchEntry() == branch and RS.fetchInstr().getType() != branchType:
                    #if this entry is one that should be cleared, do it
                    self.clearRS(self.rs.index(RS))
                    
                    

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
        dep1 = None #RAT.lookup(instr.getField2())
        dep2 = None
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
        self.populateRS(nextEntry, instr.getType(), dest, value1, value2, dep1, dep2, cycle, instr, PC, instr.getBranchEntry())
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
    def exeInstr(self, cycle, CDB):
        #first check if an instr is actually in flight, if not, just jump out
        if self.currentExe == -1:
            return (-1,-1)
    
        #increment the count of cycles in exe stage
        self.cyclesInProgress = self.cyclesInProgress + 1
        #make sure the cycles executed thus far is still < the # it takes
        if self.cyclesInProgress < self.ex_cycles:
            #return, still need to exe for more cycles
            return (-1,-1)
        
        #else, the cycles in exe have completed, compute the actual result and send it over the CDB to ROB and release RS
        result = None
        curOp = self.rs[self.currentExe].fetchOp()
        if curOp == "ADD" or curOp == "ADDI":
            result = self.rs[self.currentExe].fetchValue1() + self.rs[self.currentExe].fetchValue2()
        elif curOp == "SUB" or curOp == "BEQ" or curOp == "BNE":
            #use subtraction for branch instructions as well, BEQ if Rs - Rt = 0 and BNE if Rs - Rt != 0
            result = self.rs[self.currentExe].fetchValue1() - self.rs[self.currentExe].fetchValue2()
        
        
        print("Result of ", self.rs[self.currentExe].fetchInstr(), " is ", str(result))
        #saving these 2 values now before they are cleared, for branch instruction resolution
        instrPC = self.rs[self.currentExe].fetchInstr().getPC()
        instrField3 = self.rs[self.currentExe].fetchInstr().getField3()
        
        #send to CDB buffer and clear FU, mark RS done
        CDB.newIntAdd(self.rs[self.currentExe], result, cycle)
        self.rs[self.currentExe].fetchInstr().setExEnd(cycle)
        self.rs[self.currentExe].markDone()
        self.currentExe = -1
        self.cyclesInProgress = 0
        
        return (result, instrPC, instrField3)
        
    #method to grab the instruction currently being executed (if any)
    def clearSpeculativeExe(self, entryToClear):
        #first check if an instr is actually in flight, if not, just jump out
        if self.currentExe == -1:
            return -1
            
        #print("entryToClear = ", entryToClear)
        
        #otherwise, check if the instruction being executed was a recently resolved mispredicted branch, if so, kill it
        if self.rs[self.currentExe].fetchInstr().getBranchEntry() == entryToClear:
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

        self.populateRS(nextEntry, instr.getType(), dest, value1, value2, dep1, dep2, cycle, instr, PC, instr.getBranchEntry())
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
            if self.rs[idx].fetchInstr().getBranchEntry() == entryToClear:
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

        self.populateRS(nextEntry, instr.getType(), dest, value1, value2, dep1, dep2, cycle, instr, PC, instr.getBranchEntry())
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
            if self.rs[idx].fetchInstr().getBranchEntry() == entryToClear:
                self.executing[idx] = -1

class LSQueueEntry():
    def __init__(self):
        self.LoadOrStore = None #holds type of the instruction
        self.PC = None #holds PC of the instruction
        self.sequence = None #holds sequence number (CYCLE) of instruction so we keep them in order
        self.address = None #calculated memory address for storing or loading
        self.dep1 = None #dependency for value being stored - Field1
        self.dep2 = None #dependency for value used to calculate address - Field3
        self.value1 = None #this holds the value for Fa in stores -> value to be stored
        self.value2 = None #this holds the value for Ra in LD/SD, calculate value of address with -> offset(Ra)
        self.offset = None #going to just make a variable for this for ease of access
        self.result = None #value to store or value loaded from memory 
        self.instruction = None #holding instruction here as well for checking branches
        self.ROBEntry = None #using the ROB entry to resolve
        
    #method to populate the fields of an entry
    def populateEntry(self, PC, dep1, dep2, value1, value2, instruction, cycle):
        self.LoadOrStore = instruction.getType() #grab LD or SD
        self.PC = PC 
        self.sequence = cycle #sequence is just the order of entries, sort of redundant, but can identify by cycle numbers
        #not updating address yet, that is calculated in EXE stage
        self.dep1 = dep1 #possible dependency 1, only present for SD instructions
        self.dep2 = dep2 #possible dependency 2, present for both LD and SD
        self.value1 = value1 #this holds the value for Fa in stores -> value to be stored
        self.value2 = value2 #this holds the value for Ra in LD/SD, calculate value of address with -> offset(Ra)
        self.offset = instruction.getField2() #grab offset from instruction just for easier use
        self.instruction = instruction
        
    #method to populate the address since it is not known when entry is first created/filled
    def updateAddress(self, address):
        self.address = address
        
    #method to update dependency 1
    def updateDep1(self, dep1):
        self.dep1 = dep1
    
    #method to update dependency 2
    def updateDep2(self, dep2):
        self.dep2 = dep2
        
    #method to populate the value since it may not be known when entry is first created/filled
    def updateValue(self, value):
        self.value = value
        
    #method to check if the entry is a load or store
    def getLS(self):
        return self.LoadOrStore
    
    #method to check the address within an entry
    def getAddress(self):
        return self.address
        
    #method to check value of within an entry
    def getValue(self):
        return self.value
        
    #method to return the address this entry corresponds to
    def getInstruction(self):
        return self.instruction
        

class LoadStoreQueue():
    def __init__(self):
        self.head = 0 #location of the top of the FIFO
        self.tail = 0 #location of the end of the FIFO (next place to fill an entry, not occupied)
        self.entries = [] #actual entries within the LSQ
        for i in range(250): #please don't ever reach 250 entries
            self.entries.append(LSQueueEntry())
        
    #method to add an entry to the queue
    def addEntry(self, PC, dep1, dep2, value1, value2, instr, cycle):
        # head=tail means empty or full, if head is a valid entry, then full
        if self.isFull():
            print("Load Store Queue is full, cannot insert the newest entry!")
            
        self.entries[self.tail].populateEntry(PC, dep1, dep2, value1, value2, instr, cycle)
        self.tail = self.tail + 1 #increment tail value
        
    #method to pop an entry from the queue - ONLY DONE IN FIFO MANNER
    def popEntry(self):
        #check if empty first
        if self.entries[self.head].getLS() == None:
            print("Trying to pop the oldest entry in LS Queue but it is empty!")
    
        self.entries[self.head].clearEntry()
        self.head = self.head + 1 #make next entry the head of the queue
        
    #method to check if an entry is in use
    #def isInUse(self):
        #loop through all entries starting from head
        #for entry in self.entries
        
    #method to check if the queue is full - should never happen
    def isFull(self):
        return self.head == self.tail and self.entries[self.head].getLS() != None
        
    #method to return tail - next location for inserting an entry
    def getTail(self):
        return self.tail
        
    #method to return the entries list
    def getEntries(self):
        return self.entries

class MemoryUnit(unitWithRS):
    def __init__(self, rs_count: int, ex_cycles: int, mem_cycles: int, fu_count: int) -> None:
        self.rs_count = rs_count
        self.ex_cycles = ex_cycles
        self.mem_cycles = mem_cycles
        self.fu_count = fu_count
        self.queue = LoadStoreQueue()
        self.memory = [None] * 64 #256 Bytes -> 64 Words
            
    #method to update memory value
    def updateMemory(self, address, newValue):
        #check if address is > 256 which is the limit
        if address > 256:
            print("Trying to update a memory value beyond the 256 Bytes! Value: ", address)
        #address will be byte addressed e.g. 0,4,8, so divide by 4 for word addressed
        self.memory[address/4] = newValue
        
    #method to grab a requested memory value
    def getMemory(self, address):
        #check if address is > 256 which is the limit
        if address > 256:
            print("Trying to fetch a memory value beyond the 256 Bytes! Value: ", address)
        #address will be byte addressed e.g. 0,4,8, so divide by 4 for word addressed
        return self.memory[address/4]    
    
    #method to check if any available entries in queue
    def nextAvailableEntry(self):
        #check if full, if yes, return -1
        if self.queue.isFull():
            return -1
        #otherwise, return the next entry to insert an item
        return self.queue.getTail()
    
    #method to add an entry to the queue
    def addEntry(self, PC, dep1, dep2, value, instr, cycle):
        self.queue.addEntry(PC, dep1, dep2, value, instr, cycle)
        
    #method to pop an entry from the queue - ONLY DONE IN FIFO MANNER
    def popEntry(self):
        self.queue.popEntry()
        
    #method to (try) and issue instructions
    def issueInstruction(self, instr, cycle, RAT, fpARF, robAlias, ROB, PC):
        #grab the next available entry in the LS Queue
        nextEntry = self.nextAvailableEntry()
        if nextEntry == -1:
            raise Exception("Load/Store Queue attempting to issue with no available entries")
        
        #declare these variables outside the if statements then populate within
        dep1 = None
        dep2 = None
        value1 = None
        value2 = None
        
        #have different cases for handling dependencies between loads and stores
        if instr.getType() == "LD":
            #if load, looks like this: LD Fa, offset(Ra), where we are loading value at addr offset+Ra into Fa
            #thus, depend upon Ra before we can perform the address computation
            dep1 = None #this will correspond to the offset value - which is just a hard-coded value
            dep2 = RAT.lookup(instr.getField3()) #this corresponds to the Ra within the instruction
            #now update the RAT with the new destination
            RAT.update(instr.getField1(), robAlias)
            dest = RAT.lookup(instr.getField1())
            #check if we can resolve the dependency (dep2) right away in 2 ways - no need to solve dep1 as it isnt a dependency
            #1. check if the dependency is just the original register name in the ARF
            if dep2 == instr.getField3():
                dep2 = "None"
                value2 = fpARF.lookup(instr.getField3())
            #2. check if value exists in ROB but hasn't been committed yet
            if ROB.searchEntries(dep2) != None:
                value2 = ROB.searchEntries(dep2)
                dep2 = "None"
        else:
            #else, it is a store and looks like this: SD Fa, offset(Ra), storing value in Fa to addr offset+Ra
            #thus, depend on both Fa and Ra
            dep1 = RAT.lookup(instr.Field1()) #this dependency is for the value being stored - Fa
            dep2 = RAT.lookup(instr.getField3()) #this corresponds to the Ra within the instruction
            #no need to update RAT for the store instruction, nothing is going to be written back
            #check if we can resolve the dependencies right away in 2 ways
            #1. check if the dependency is just the original register name in the ARF
            if dep1 == instr.getField1():
                dep1 = "None"
                value1 = fpARF.lookup(instr.getField1())
            if dep2 == instr.getField3():
                dep2 = "None"
                value2 = fpARF.lookup(instr.getField3())
            #2. check if value exists in ROB but hasn't been committed yet
            if ROB.searchEntries(dep1) != None:
                value1 = ROB.searchEntries(dep1)
                dep1 = "None"
            if ROB.searchEntries(dep2) != None:
                value2 = ROB.searchEntries(dep2)
                dep2 = "None"
                
        #finally, add this instruction to the load/store queue
        self.addEntry(PC, dep1, dep2, value1, value2, instr, cycle)

        self.populateRS(nextEntry, instr.getType(), dest, value1, value2, dep1, dep2, cycle, instr, PC, instr.getBranchEntry())
        print("FpMult RS ", str(nextEntry), " update: ", self.rs[nextEntry])
    
            
    