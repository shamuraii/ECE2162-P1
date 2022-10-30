from architecture import ReservationStation

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
    def populateRS(self, entry, op, value1, value2, dep1, dep2):
        #populate fields of chosen RS
        self.rs[entry].updateBusy(1) #mark this RS as now being populated/busy doing computation
        self.rs[entry].updateOp(op) #will hold instruction in use
        self.rs[entry].updateValue1(value1) #will either be a reg. value or placeholder until dep is resolved
        self.rs[entry].updateValue2(value2) #same as line above
        self.rs[entry].updateDep1(dep1) #will be empty or an ROB entry
        self.rs[entry].updateDep2(dep2) #empty or an ROB entry
        
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
        if self.rs[entry].fetchDep1() == dep:
            self.rs[entry].updateValue1(value) #update to resolved value
            self.rs[entry].updateDep1("None") #clear dependency
        elif self.rs[entry].fetchDep2() == dep:
            self.rs[entry].updateValue2(value) #update to resolved value
            self.rs[entry].updateDep2("None") #clear dependency   
        
        
    #method to clear a RS once it completes
    def clearRS(self, entry):
        self.rs[entry].clearEntry()

    def printRS(self):
        for i in self.rs:
            i.print()


class IntAdder(unitWithRS):
    def __init__(self, rs_count: int, ex_cycles: int, fu_count: int) -> None:
        self.rs_count = rs_count
        self.ex_cycles = ex_cycles
        self.fu_count = fu_count
        self.rs = []
        for i in range(rs_count):
            self.rs.append(ReservationStation())

    def __str__(self) -> str:
        pass


class FloatAdder(unitWithRS):
    def __init__(self, rs_count: int, ex_cycles: int, fu_count: int) -> None:
        self.rs_count = rs_count
        self.ex_cycles = ex_cycles
        self.fu_count = fu_count
        self.rs = []
        for i in range(rs_count):
            self.rs.append(ReservationStation())
            

class FloatMult(unitWithRS):
    def __init__(self, rs_count: int, ex_cycles: int, fu_count: int) -> None:
        self.rs_count = rs_count
        self.ex_cycles = ex_cycles
        self.fu_count = fu_count
        self.rs = []
        for i in range(rs_count):
            self.rs.append(ReservationStation())
    

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
            
    def print(self):
        #print all registers and their values
        for key, value in self.registers.items():
            print(key, ' : ', value)
            
class FloatingPointARF:
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
            
    def print(self):
        #print all registers and their values
        for key, value in self.registers.items():
            print(key, ' : ', value)

class MemoryUnit(unitWithRS):
    def __init__(self, rs_count: int, ex_cycles: int, mem_cycles: int, fu_count: int) -> None:
        self.rs_count = rs_count
        self.ex_cycles = ex_cycles
        self.mem_cycles = mem_cycles
        self.fu_count = fu_count
        self.rs = []
        for i in range(rs_count):
            self.rs.append(ReservationStation())
            
