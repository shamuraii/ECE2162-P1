from units import IntAdder, FloatAdder, FloatMult, MemoryUnit
from architecture import ReorderBuffer

class CommonDataBus:
    def __init__(
        self,
        buffSize,
        intAdder: IntAdder,
        fpAdder: FloatAdder,
        fpMult: FloatMult,
        lsUnit: MemoryUnit,
        ROB: ReorderBuffer
    ) -> None:
        # buffers are lists of tuples (ReservationStationEntry, value, cycle_finished)
        self.buffSize = buffSize 
        self.intAddBuff = []
        self.fpAddBuff = []
        self.fpMultBuff = []
        self.memBuff = []
        self.intAdder = intAdder
        self.fpAdder = fpAdder
        self.fpMult = fpMult
        self.lsUnit = lsUnit
        self.ROB = ROB

    def newIntAdd(self, station, value, cycle):
        if len(self.intAddBuff) >= self.buffSize:
            raise Exception("CDB Buffer Filled (IntAdd)")
        else:
            self.intAddBuff.append((station, value, cycle))

    def newFpAdd(self):
        pass

    def newFpMult(self):
        pass
    
    def newMem(self):
        pass

    def writeBack(self, cycle):
        # combine all the buffers
        allBuffs = [*self.intAddBuff, *self.fpAddBuff, *self.fpMultBuff, *self.memBuff]
        if len(allBuffs) == 0:
            #nothing is waiting to writeback
            return

        # find oldest instruction
        allBuffs.sort(key=lambda x: x[0].fetchCycle())
        for buff in allBuffs:
            wbStation, wbValue, doneCycle = buff
            wbDest = wbStation.fetchDest()
            if doneCycle == cycle:
                continue # cannot writeback same cycle added, try another instruction
            
            print("CDB WritingBack: ", wbStation, " | val=", wbValue)

            #update instruction wbCycle
            wbStation.fetchInstr().setWbCycle(cycle)
            #want to save the instr before it is deleted in case it was a branch or ld/sd
            instr = wbStation.fetchInstr()

            #update all RS in all units (unit should delete station entry)
            self.intAdder.writebackRS(wbStation, wbValue)
            #fpadder
            #fpmult
            #etc
            
            #update ROB entry, need special cases for branches and loads/stores since they're not "conventional" instrs
            if instr.getType() == "BNE" or instr.getType() == "BEQ":
                #don't actually need to WB a branch
                self.ROB.writebackROBBranch(instr, cycle)
            else:
                self.ROB.writebackROB(wbDest, wbValue, cycle)

            #remove from whichever CDB buffer it came from
            if buff in self.intAddBuff: self.intAddBuff.remove(buff)
            if buff in self.fpAddBuff: self.fpAddBuff.remove(buff)
            if buff in self.fpMultBuff: self.fpMultBuff.remove(buff)
            if buff in self.memBuff: self.memBuff.remove(buff)
            #only writeback once per cycle
            break
