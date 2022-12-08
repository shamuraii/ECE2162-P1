
class BTBEntry:
	def __init__(self):
		self.predictedPC = 0 #predicted PC to jump to if branch taken
		self.targetBits = 0 #bottom 3 bits of target address
		self.branchPredict = 0 #simple one-bit predictor
		
	def __str__(self) -> str:
		return "\t".join([str(self.PC), str(self.predictedPC), str(self.branchPredict)])

	#method to update the predicted branch result
	def updatePrediction(self, PC, branchResult, offset, mode):
		#check the current 1-bit predictor state
		if self.branchPredict == 1 and branchResult == 0: #if branch was predicted taken, but actually wasn't, update
			#branch not taken, only change flag to not taken, do not update target address
			self.branchPredict = 0
			return -1
		elif self.branchPredict == 0 and branchResult == 1: #if branch was predicted not taken, but actually wasn't, update
			#branch taken, change prediction bit
			self.branchPredict = 1
			#also update the predicted PC to reflect this change
			return self.calculatePredictedPC(PC, offset, mode)
		#don't need to worry about the other cases since it's only a 1-bit predictor 

	#calculate the predicted PC - called upon filling BTBEntry, as well as when changing the prediction bit
	def calculatePredictedPC(self, PC, offset, mode):
		#mode 1 for calculating: byte address calculation - only including this for if the professor uses byte addressed PC
		if mode == 1:
			#check if branch is predicted to be taken or not, and update predicted PC accordingly
			if self.branchPredict == 1: #branch is predicted to be taken
				#new PC = PC+4+offset<<2
				bytePC = ((PC*4) + 4 + int(offset)) << 2 #byte addressed PC
				self.predictedPC = bytePC / 4 #convert back to "regular" notation by dividing by 4, the number of bytes per PC entry
		else: #else, can just use normal "relative" addressing, ie PC goes 0,1,2,3,4,5,etc
			#check if branch is predicted to be taken or not, and update predicted PC accordingly
			if self.branchPredict == 1: #branch is predicted to be taken
				#new PC = PC+1+offset
				self.predictedPC = PC + 1 + int(offset) 
				#print("self.predictedPC before: ", self.predictedPC)
				#take bottom 3 bits and store as BTB target bits ************************
				self.targetBits = self.predictedPC & 7
				#print("self.targetBits: ", self.targetBits)
				#now recalculate the predicted PC as the branch PC with the bottom 3 bits as the target Bits
				#create a bitmask for the top 29 bits of PC
				mask = ~0xf
				mask = mask | 0x8
				#now use the mask to preserve all bits from PC but bottom 3
				self.predictedPC = self.predictedPC & mask
				#finally, use bitwise OR to place the target bits in the bottom 3 bit slots
				self.predictedPC = self.predictedPC | self.targetBits
				#print("self.predictedPC after: ", self.predictedPC)
				return self.predictedPC
			
				
		#not going to do the byte addressing [PC+4+offset<<2] method, just relative
		#e.g. going from instr 7 to 0 -> 7+1-8=0, can use offset directly
		
	#grab predicted PC for this entry
	def getPredictedPC(self, PC):
		#create a bitmask for the top 29 bits of PC
		mask = ~0xf
		mask = mask | 0x8
		#print("mask is: ", mask)
		#print("PC before: ", PC)
		#now use the mask to preserve all bits from PC but bottom 3
		PC = PC & mask
		#print("PC after mask: ", PC)
		#finally, use bitwise OR to place the target bits in the bottom 3 bit slots
		PC = PC | self.targetBits
		#print("PC after adding target bits: ", PC)
		#print("self.targetBits: ", self.targetBits)
		return PC
		
	#grab the prediction for this branch - taken or not taken
	def getPrediction(self):
		return self.branchPredict   
        

class BTB:
    def __init__(self):
        self.entries = [] #the entries in the BTB, will have 4 total
        for i in range(4):
            self.entries.append(BTBEntry())
            
    def __str__(self):
        return '\n'.join(str(entry) for entry in self.entries)
        
    #method to update the branch prediction of the given entry
    def updateEntryPrediction(self, entry, PC, result, offset, mode):
        return self.entries[entry].updatePrediction(PC, result, offset, mode)
        
    #grab the predicted PC for a given entry
    def getEntryPredictedPC(self, entry, PC):
        return self.entries[entry].getPredictedPC(PC)
        
    #grab the prediction for taking the branch or not
    def getBranchPrediction(self, entry):
        return self.entries[entry].getPrediction()
        
        
#primary branch predictor class
class BranchPredictor:
    def __init__(self) -> None:
        self.BTB = BTB()
        print("Using P2 Branch Predictor!")
        
    def print(self):
        print(self.BTB)

    #method to update the BTB based on branch result
    def updateBTB(self, PC, result, offset, mode):
        #grab BTB entry related to this PC
        entry = self.getEntry(PC)

        #update the branch result for taken or not taken, if taken, also update target bits
        return self.BTB.updateEntryPrediction(entry, PC, result, offset, mode)
            
    #method to return the listed PC of a branch
    def getEntryPC(self, PC):
        #first grab the entry it should be located in
        entry = self.getEntry(PC)
        return int(self.BTB.getEntryPredictedPC(entry, PC))
    
    #method to just return if a branch is predicted taken (1) or not (0)
    def getEntryBranchPrediction(self, PC):
        #first grab the entry it should be located in
        entry = self.getEntry(PC)
        return self.BTB.getBranchPrediction(entry)
        
    #find which entry in the BTB this PC belongs to
    def getEntry(self, PC):
        return PC & 3 #bitwise value AND 000...00011 to get lowest 2 bits
        
        
        
        
        
        
        