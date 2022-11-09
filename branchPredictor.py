
class BTBEntry:
    def __init__(self):
        self.PC = -1 #address/PC of the branch instruction
        self.predictedPC = -1 #predicted PC to jump to if branch taken
        self.branchPredict = -1 #simple one-bit predictor
        
    def __str__(self) -> str:
        return "\t".join([str(self.PC), str(self.predictedPC), str(self.branchPredict)])
        
    #method to fill in fields of the BTBEntry 
    def fillEntry(self, PC):
        self.PC = PC
        #not worrying about assigning predictedPC here as that will be done when updatePrediction is called right after this
        #self.predictedPC = 0
        self.branchPredict = 0 #doesn't matter what we set this to, it will be updated directly after populating entry
    
    #method to update the predicted branch result
    def updatePrediction(self, branchResult, offset, mode):
        #check the current 1-bit predictor state
        if self.branchPredict == 1 and branchResult == 0: #if branch was predicted taken, but actually wasn't, update
            self.branchPredict = 0
            #also update the predicted PC to reflect this change
            self.calculatePredictedPC(offset, mode)
        elif self.branchPredict == 0 and branchResult == 1: #if branch was predicted not taken, but actually wasn't, update
            self.branchPredict = 1
            #also update the predicted PC to reflect this change
            self.calculatePredictedPC(offset, mode)
        #don't need to worry about the other cases since it's only a 1-bit predictor 
    
    #calculate the predicted PC - called upon filling BTBEntry, as well as when changing the prediction bit
    def calculatePredictedPC(self, offset, mode):
        #mode 1 for calculating: byte address calculation - only including this for if the professor uses byte addressed PC
        if mode == 1:
            #check if branch is predicted to be taken or not, and update predicted PC accordingly
            if self.branchPredict == 1: #branch is predicted to be taken
                #new PC = PC+4+offset<<2
                bytePC = ((self.PC*4) + 4 + int(offset)) << 2 #byte addressed PC
                self.predictedPC = bytePC / 4 #convert back to "regular" notation by dividing by 4, the number of bytes per PC entry
            else: #else branch is predicted to be NOT taken
                #new PC = PC+4
                self.predictedPC = self.PC + 1 #not gonna bother with adding 4 then div by 4
        else: #else, can just use normal "relative" addressing, ie PC goes 0,1,2,3,4,5,etc
            #check if branch is predicted to be taken or not, and update predicted PC accordingly
            if self.branchPredict == 1: #branch is predicted to be taken
                #new PC = PC+1+offset
                self.predictedPC = self.PC + 1 + int(offset) 
            else: #else branch is predicted to be NOT taken
                #new PC = PC + 1
                self.predictedPC = self.PC + 1 
            
                
        #not going to do the byte addressing [PC+4+offset<<2] method, just relative
        #e.g. going from instr 7 to 0 -> 7+1-8=0, can use offset directly
    
    #set the predicted PC for this entry
    def setPredictedPC(self, newPC):
        self.predictedPC = newPC
    
    #grab PC for this entry
    def getPC(self):
        return self.PC
        
    #grab predicted PC for this entry
    def getPredictedPC(self):
        return self.predictedPC
        
    #grab the prediction for this branch - taken or not taken
    def getPrediction(self):
        return self.branchPredict   
        

class BTB:
    def __init__(self):
        self.entries = [] #the entries in the BTB, will have 8 total
        for i in range(8):
            self.entries.append(BTBEntry())
            
    def __str__(self):
        return '\n'.join(str(entry) for entry in self.entries)
            
    #populate an entry in the BTB
    def populateEntry(self, entry, PC):
        self.entries[entry].fillEntry(PC)
        
    #method to update the branch prediction of the given entry
    def updateEntryPrediction(self, entry, result, offset, mode):
        self.entries[entry].updatePrediction(result, offset, mode)
        
    #grab the address/PC for a given entry
    def getEntryPC(self, entry):
        return self.entries[entry].getPC()
        
    #grab the predicted PC for a given entry
    def getEntryPredictedPC(self, entry):
        return self.entries[entry].getPredictedPC()
        
    #grab the prediction for taking the branch or not
    def getBranchPrediction(self, entry):
        return self.entries[entry].getPrediction()
        
        
#primary branch predictor class
class BranchPredictor:
    def __init__(self) -> None:
        self.BTB = BTB()
        
    def print(self):
        print(self.BTB)

    #method to update the BTB based on branch result
    def updateBTB(self, PC, result, offset, mode):
        #see if entry already existed for this PC
        entry = self.getEntry(PC)
        #if this PC is in the BTB, just update the related branch prediction bit
        if self.BTB.getEntryPC(entry) == PC:
            self.BTB.updateEntryPrediction(entry, result, offset, mode)
        else:
            #else, this PC must be added to the BTB as its own entry
            self.BTB.populateEntry(entry, PC)
            #also update the branch result in the event of not taken, since the BTB entry initializes to taken
            self.BTB.updateEntryPrediction(entry, result, offset, mode)
            
    #method to return the listed PC of a branch
    def getEntryPC(self, PC):
        #first grab the entry it should be located in
        entry = self.getEntry(PC)
        return int(self.BTB.getEntryPredictedPC(entry))
    
    #method to just return if a branch is predicted taken (1) or not (0)
    def getEntryBranchPrediction(self, PC):
        #first grab the entry it should be located in
        entry = self.getEntry(PC)
        return self.BTB.getBranchPrediction(entry)
        
    #find which entry in the BTB this PC belongs to
    def getEntry(self, PC):
        return PC & 7 #bitwise value AND 000...00111 to get lowest 3 bits
        
        
        
        
        
        
        