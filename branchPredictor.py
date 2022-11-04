
class BTBEntry:
    def __init__(self):
        self.PC = -1 #address/PC of the branch instruction
        self.predictedPC = -1 #predicted PC to jump to if branch taken
        self.branchPredict = -1 #simple one-bit predictor
        
    #method to fill in fields of the BTBEntry - should only ever need to update the branch prediction
    def fillEntry(self, PC, targetPC):
        self.PC = PC
        self.predictedPC = targetPC 
        self.branchPredict = 1 #set branch prediction to be taken to start
    
    #method to update the predicted branch result
    def updatePrediction(self, branchResult):
        #check the current 1-bit predictor state
        if self.branchPredict == 1 and branchResult == 0: #if branch was predicted taken, but actually wasn't, update
            self.branchPredict = 0
        elif self.branchPredict == 0 and branchResult == 1: #if branch was predicted not taken, but actually wasn, update
            self.branchPredict = 1
        #don't need to worry about the other cases since it's only a 1-bit predictor 
    
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
            
    #populate an entry in the BTB
    def populateEntry(self, entry, PC, targetPC):
        self.entries[entry].fillEntry(PC, targetPC)
        
    #method to update the branch prediction of the given entry
    def updateEntryPrediction(self, entry, result):
        self.entries[entry].updatePrediction(result)
        
    #grab the address/PC for a given entry
    def getEntryPC(self, entry):
        return self.entries[entry].getPC()
        
    #grab the predicted PC for a given entry
    def getEntryPredictedPC(self, entry):
        return self.entries[entry].getPredictedPC()
        
    #grab the prediction for taking the branch or not
    def getBranchPrediction(self, entry):
        return self.entries[entry].getPrediction()
        
        
#primary branch predictor class, will be calling isBranch and updateBTB only
class BranchPredictor:
    def __init__(self) -> None:
        self.BTB = BTB()
        
    #method to add new entry to the BTB
    #def addEntry(self, PC, targetPC):
        #first grab the entry it should be added into
        #entry = self.getEntry(PC)
        #then add this branch into the BTB
        #self.BTB.populateEntry(entry, PC, targetPC)
        
    #check if a given PC is predicted as a branch, return -1 if no branch/not taken, or new PC if taken
    def isBranchTaken(self, PC):
        #first grab the entry it should be located in
        entry = self.getEntry(PC)
        #next check if the stored address is the same as the one we're looking at right now
        if self.BTB.getEntryPC(entry) == PC:
            #this instruction is a branch, now check if we predict to take the branch or not
            prediction = self.BTB.getBranchPrediction(entry)
            #if yes, return the predicted PC
            if prediction == 1:
                return self.BTB.getEntryPredictedPC(entry)
            #if no, PC will continue as PC+4 as expected, just return -1 to signify branch not taken
        #if the stored address is NOT the same as the PC in question (or not found), then assume it is not a branch, thus PC=PC+4
        return -1

    #method to update the BTB based on branch result
    def updateBTB(self, PC, targetPC, result):
        #see if entry already existed for this PC
        entry = self.getEntry(PC)
        #if this PC is in the BTB, just update the related branch prediction bit
        if self.BTB.getEntryPC(entry) == PC:
            self.BTB.updateEntryPrediction(entry, result)
        else:
            #else, this PC must be added to the BTB as its own entry
            self.BTB.populateEntry(entry, PC, targetPC)
            #also update the branch result in the event of not taken, since the BTB entry initializes to taken
            self.BTB.updateEntryPrediction(entry, result)
        
    #find which entry in the BTB this PC belongs to
    def getEntry(self, PC):
        return PC & 7 #bitwise value AND 000...00111 to get lowest 3 bits
        
        
        
        
        
        
        