         
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
            
    def update(self, register, newAlias):
        #first check for valid register
        if register in self.entries:
            #update the register value
            self.entries[register] = newAlias
        else:
            print("REGISTER " + register + " INVALID - CANNOT UPDATE RAT")
            
    def print(self):
        #print all int reg aliases
        for key, value in self.entries.items():
            print(key, ' : ', value)


class ReservationStation:
    def __init__(self) -> None:
        self.busy = 0 #0 = not busy/not in use, 1 = busy/in use
        self.op = "None" #will hold the instruction type
        self.value1 = 0 #value of reg/arg 1
        self.value2 = 0 #value of reg/arg 2
        self.dep1 = "None" #holds physical register of dependency 1 - corresponds to value 1
        self.dep2 = "None" #holds physical register of dependency 2 - corresponds to value 2
        self.addr = 0 #holds address for load/store instructions
    
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
    
    #returns dependencies of the RS
    def fetchDep1(self):
        return self.dep1
    def fetchDep2(self):
        return self.dep2
    
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
        
    def print(self):
        print(str(self.busy) +"\t"+ str(self.op) +"\t"+ str(self.value1) +"\t"+ str(self.value2) +"\t"+ str(self.dep1) +"\t"+ str(self.dep2) +"\t"+ str(self.addr))
    

class ReorderBuffer:
    def __init__(self, entries) -> None:
        
        pass


class Instruction:
    def __init__(self, type, field1, field2, field3):
        self.type = type
        self.field1 = field1
        self.field2 = field2
        self.field3 = field3
    
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
        return self.field1
    
    def getField2(self):
        return self.field2
    
    def getField3(self):
        return self.field3
    
    #print statement for instruction
    def print(self):
        if self.type != "NOP" and self.type != "SD" and self.type != "LD": 
            print(self.type +' '+ str(self.field1) +','+ str(self.field2) +','+ str(self.field3))
        elif self.type == "SD" or self.type == "LD":
            print(self.type +' '+ str(self.field1) +','+ str(self.field2) +'('+ str(self.field3) + ')')
        else:
            print(self.type)

class InstructionBuffer:
    def __init__(self, length) -> None:
        self.buffer = [] #list of instrs
        #initialize the instruction buffer of length "length"
        for i in range(length):
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
        self.buffer[entry].clearInstr()
        
    #method to print contents of buffer
    def print(self):
        #loop through entire buffer and print every entry
        for entry in self.buffer:
            entry.print()
                
        
class CommonDataBus:
    def __init__(self) -> None:
       pass 
        
class BranchPredictor:
    def __init__(self) -> None:
        pass