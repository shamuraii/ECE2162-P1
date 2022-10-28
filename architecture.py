         
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
        pass

class ReorderBuffer:
    def __init__(self) -> None:
        pass

class InstructionBuffer:
    def __init__(self) -> None:
        pass
        
class CommonDataBus:
    def __init__(self) -> None:
       pass 
        
class BranchPredictor:
    def __init__(self) -> None:
        pass