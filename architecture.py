
class RegisterAliasTable:
    #using a dict here for unique-ness, can't have 2 R10s for instance
    entries = {}
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
            self.entries[register] = newAlias
        else:
            print("REGISTER " + register + " INVALID - CANNOT UPDATE RAT")
            
    #method to lookup registers
    def lookup(self, register):
        #assuming register found in RAT, return its alias 
        if register in self.entries:
            return self.entries[register]
            
    #print all registers and their aliases
    def __str__(self):
        #print all int reg aliases
        return '\n'.join([str(key, ' : ', value) for key, value in self.entries.items()])

class ReservationStation:
    def __init__(self) -> None:
        self.busy = 0 #0 = not busy/not in use, 1 = busy/in use
        self.op = "None" #will hold the instruction type
        self.value1 = 0 #value of reg/arg 1
        self.value2 = 0 #value of reg/arg 2
        self.dep1 = "None" #holds physical register of dependency 1 - corresponds to value 1
        self.dep2 = "None" #holds physical register of dependency 2 - corresponds to value 2
        self.addr = 0 #holds address for load/store instructions
        self.cycle = 0 #holds cycle issued to ensure we do not issue and begin execution on same cycle 
    
    def __str__(self):
        return "\t".join(self.busy, self.op, self.value1, self.value2, self.dep1, self.dep2, self.addr)

    #returns if this given RS is busy or not
    def checkBusy(self):
        return self.busy
        
    #clears all fields of the RS for reuse
    def clearEntry(self):
        self.busy = 0 
        self.op = "None" 
        self.value1 = 0 
        self.value2 = 0 
        self.dep1 = "None" 
        self.dep2 = "None" 
        self.addr = 0
        self.cycle = 0
    
    #returns dependencies of the RS
    def fetchDep1(self):
        return self.dep1
    def fetchDep2(self):
        return self.dep2
    #method returns True if dependencies exist or False if dependencies do not exist
    def areThereDeps(self):
        if self.fetchDep1() != "None" or self.fetchDep2() != "None":
            return True
        else:
            return False
            
    #methods to return fields w/ values for computation
    def fetchValue1(self):
        return self.value1
    def fetchValue2(self):
        return self.value2
        
    #method to fetch op to ensure what's going on
    def fetchOp(self):
        return self.op            
    
    #method to fetch what cycle this instruction was issued on
    def fetchCycle(self):
        return self.cycle
    
    #creating update methods for each because we do not know what will be set initially
    #may have 1 value & 1 dep, 0 value & 2 dep, just an address, etc 
    
    def updateBusy(self, newBusy):
        self.busy = newBusy
    
    def updateOp(self, newOp):
        self.op = newOp
        
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

    
class ROBEntry:
    def __init__(self, op, dest, value):
        self.op = op
        self.dest = dest
        self.value = value
        self.done = 0

    def __str__(self) -> str:
        return "\t".join(self.op, self.dest, self.value, self.done)

    def updateValue(self, newValue):
        if self.done: raise Exception("Attempting to update a ROB value that is already completed: ", ",".join(self.op, self.dest, self.value))
        # Update value and mark as done
        self.value = newValue
        self.done = 1

    def getOp(self):
        return self.op

    def getDest(self):
        return self.dest

    def getValue(self):
        return self.value

    def getDone(self):
        return self.done


class ReorderBuffer:
    def __init__(self, length: int) -> None:
        self.length = length
        self.entries = [None] * length
        self.head = 0
        self.tail = 0

    def isEmpty(self) -> bool:
        # If oldest instruction is None, all are None
        return self.entires[self.tail] == None

    def isFull(self) -> bool:
        # head=tail means empty or full, if head is a valid entry, then full
        return (self.head == self.tail and self.entries[self.head] != None)

    def addEntry(self, op, dest, value) -> str:
        # Shouldn't occur, Check ROB before adding. This functionality could be changed though
        if self.isFull(): raise Exception("Attempting to add entry to FULL ROB: ", ",".join(op, dest, value))
        # Add new entry at head and increment head
        self.entries[self.head] = ROBEntry(op, dest, value)
        outstr = "ROB" + str(self.head)
        self.head = (self.head + 1) % self.length
        # return "ROB#" where entry was added
        return outstr
    
    def canCommit(self) -> bool:
        # return true if oldest entry exists and is done
        if self.isEmpty():
            return False
        else:
            return self.entries[self.tail].getDone()

    def getOldestEntry(self) -> ROBEntry:
        # Return the oldest instruction (could be None)
        return self.entries[self.tail]

    def deleteOldest(self):
        if self.isEmpty(): raise Exception("Attempting to remove entry from EMPTY ROB!")
        self.entries[self.tail] = None
        self.tail = (self.tail + 1) % self.length


class Instruction:
    def __init__(self, type, field1, field2, field3):
        self.type = type
        self.field1 = field1
        self.field2 = field2
        self.field3 = field3
        self.isCycle = "X"
        self.exCycle = ("X", "X") # (start,end) tuple
        self.memCycle = ("X", "X") # (start,end) tuple
        self.wbCycle = "X"
        self.comCycle = "X"
    
    #method to change contents of the instruction
    def changeInstr(self, type, field1, field2, field3):
        self.type = type
        self.field1 = field1
        self.field2 = field2
        self.field3 = field3
    
    #method to clear all fields within the instruction
    def clearInstr(self):
        self.type = "None"
        self.field1 = 0
        self.field2 = 0
        self.field3 = 0
     
    #getters for each part of the instruction
    def getType(self):
        return self.type
        
    def getField1(self):
        return self.field1 #destination
    
    def getField2(self):
        return self.field2
    
    def getField3(self):
        return self.field3

    def setIsCycle(self, val):
        self.isCycle = val
    
    def setExStart(self, val):
        self.exCycle[0] = val

    def setExEnd(self, val):
        self.exCycle[1] = val

    def setMemStart(self, val):
        self.memCycle[0] = val

    def setMemEnd(self, val):
        self.memCycle[1] = val

    def setWbCycle(self, val):
        self.wbCycle = val

    def setComCycle(self, val):
        self.comCycle = val
    
    #print statement for instruction
    def __str__(self) -> str:
        if self.type != "NOP" and self.type != "SD" and self.type != "LD": 
            return self.type +' '+ str(self.field1) +','+ str(self.field2) +','+ str(self.field3)
        elif self.type == "SD" or self.type == "LD":
            return self.type +' '+ str(self.field1) +','+ str(self.field2) +'('+ str(self.field3) + ')'
        else:
            return self.type

    def longStr(self):
        return "\t".join([str(self), self.isCycle, str(self.exCycle[0] + "-" + self.exCycle[1]), str(self.memCycle[0] + "-" + self.memCycle[1]), self.wbCycle, self.comCycle])

class InstructionBuffer:
    def __init__(self, length) -> None:
        #can use a list as a queue with append and pop(index) if we would like
        self.buffer = [] #list of instrs
        #initialize the instruction buffer of length "length"
        for _ in range(length):
            self.buffer.append(Instruction("None", 0, 0, 0))
        
    #method to add instr to the buffer, will add to first possible index - can maybe delete this
    def addInstrDetails(self, type, field1, field2, field3):
        #loop through buffer for first available entry
        for entry in self.buffer:
            if entry.type == "None":
                entry.changeInstr(type, field1, field2, field3) #if empty entry, change it to this one
                
    #method to add an instruction directly, adds to the first possible entry in the buffer
    def addInstr(self, instruction):
        #loop through buffer for first available entry
        for entry in self.buffer:
            if entry.type == "None":
                entry.changeInstr(instruction.getType(), instruction.getField1(), instruction.getField2(), instruction.getField3())
                break
    
    #method to empty a buffer entry for later reuse
    def clearEntry(self, entry):
        #print("Print before clearing entry")
        #self.print()
        self.buffer.pop(entry)
        #reappend another empty entry
        self.buffer.append(Instruction("None", 0, 0, 0))
        #print("Print after clearing entry")
        #self.print()
        
    #method to check if there are entries in the instr
    def isEmpty(self):
        #consider empty as all entries containing "None" as the type
        for entry in self.buffer:
            if entry.type != "None":
                #if there is an entry that doesn't say "None" then it is a populated entry and the buffer is NOT empty
                return False
        return True #true if list is empty, false if not
        
    #method to just return the list of instructions
    def getList(self):
        return self.buffer
        
    #method to print contents of buffer
    def __str__(self):
        #concat all instruction strings
        return '\n'.join(str(entry) for entry in self.buffer)
                
        
class CommonDataBus:
    def __init__(self) -> None:
       pass 
        
class BranchPredictor:
    def __init__(self) -> None:
        pass