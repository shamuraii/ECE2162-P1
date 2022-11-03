from architecture import Instruction, RegisterAliasTable, ReservationStationEntry

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
    def populateRS(self, entry, op, dest, value1, value2, dep1, dep2, cycle, instr):
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
        
    def writebackRS(self, cdbStation, cdbValue):
        cdbDest = cdbStation.fetchDest()
        for entry in self.rs:
            #check dep 1 for match
            if entry.fetchDep1() == cdbDest:
                entry.updateValue1(cdbValue)
                entry.updateDep1("None")
            #check dep 2 for match
            if entry.fetchDep2() == cdbDest:
                entry.updateValue2(cdbValue) 
                entry.updateDep2("None")  
            #clear entry if its the one being WrittenBack
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
    def issueInstruction(self, instr: Instruction, cycle, RAT: RegisterAliasTable, intARF: IntegerARF):
        #find next available RS if there is one - do this first as the rest doesn't matter if no RS available
        nextEntry = self.availableRS()
        if nextEntry == -1:
            # This should be checked BEFORE calling this function
            raise Exception("IntAdder attempting to issue with no available RS")
        #else, nextEntry contains the first available RS entry that will be used
        
        #print("IntAdder RS " +str(nextEntry)+ " new entry: ", instr)
        
        #FIGURE OUT DEPENDENCIES HERE FOR THE REGISTERS IN USE BY CHECKING THE RAT
        dest = RAT.lookup(instr.getField1())
        dep1 = RAT.lookup(instr.getField2())
        dep2 = RAT.lookup(instr.getField3())
        value1 = None
        value2 = None
        #check if the deps are actually just the field names, if so, no deps exist, also must grab values from ARF
        if dep1 == instr.getField2():
            dep1 = "None"
            value1 = intARF.lookup(instr.getField2())
        if dep2 == instr.getField3():
            dep2 = "None"
            value2 = intARF.lookup(instr.getField3())
        
        #now populate the RS with this info - field 2 and field 3 here must be their values, if deps exist they will be overwritten
        self.populateRS(nextEntry, instr.getType(), dest, value1, value2, dep1, dep2, cycle, instr)
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
            return
    
        #make sure the cycles executed thus far is still < the # it takes
        if self.cyclesInProgress < self.ex_cycles:
            #increment the count of cycles in exe stage
            self.cyclesInProgress = self.cyclesInProgress + 1
            #return, still need to exe for more cycles
            return
        
        #else, the cycles in exe have completed, compute the actual result and send it over the CDB to ROB and release RS
        result = None
        if self.rs[self.currentExe].fetchOp() == "ADD":
            result = self.rs[self.currentExe].fetchValue1() + self.rs[self.currentExe].fetchValue2()
        elif self.rs[self.currentExe].fetchOp() == "SUB":
            result = self.rs[self.currentExe].fetchValue1() - self.rs[self.currentExe].fetchValue2()
        
        
        print("Result of ", self.rs[self.currentExe].fetchInstr(), " is ", str(result))
        
        #send to CDB buffer and clear FU, mark RS done
        CDB.newIntAdd(self.rs[self.currentExe], result, cycle)
        self.rs[self.currentExe].fetchInstr().setExEnd(cycle)
        self.rs[self.currentExe].markDone()
        self.currentExe = -1
        self.cyclesInProgress = 0
        
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


class FloatAdder(unitWithRS):
    def __init__(self, rs_count: int, ex_cycles: int, fu_count: int) -> None:
        self.rs_count = rs_count
        self.ex_cycles = ex_cycles
        self.fu_count = fu_count
        self.rs = []
        for _ in range(rs_count):
            self.rs.append(ReservationStationEntry())
            

class FloatMult(unitWithRS):
    def __init__(self, rs_count: int, ex_cycles: int, fu_count: int) -> None:
        self.rs_count = rs_count
        self.ex_cycles = ex_cycles
        self.fu_count = fu_count
        self.rs = []
        for _ in range(rs_count):
            self.rs.append(ReservationStationEntry())            

class MemoryUnit(unitWithRS):
    def __init__(self, rs_count: int, ex_cycles: int, mem_cycles: int, fu_count: int) -> None:
        self.rs_count = rs_count
        self.ex_cycles = ex_cycles
        self.mem_cycles = mem_cycles
        self.fu_count = fu_count
        self.rs = []
        for _ in range(rs_count):
            self.rs.append(ReservationStationEntry())