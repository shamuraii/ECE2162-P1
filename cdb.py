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
        if len(self.intAddBuff) > self.buffSize:
            raise Exception("CDB Buffer Filled (IntAdd)")
        else:
            self.intAddBuff.append((station, value, cycle))

    def newFpAdd(self, station, value, cycle):
        if len(self.fpAddBuff) > self.buffSize:
            raise Exception("CDB Buffer Filled (FpAdd)")
        else:
            self.fpAddBuff.append((station, value, cycle))

    def newFpMult(self, station, value, cycle):
        if len(self.fpMultBuff) > self.buffSize:
            raise Exception("CDB Buffer Filled (FpAdd)")
        else:
            self.fpMultBuff.append((station, value, cycle))
    
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

            #update all RS in all FUs with dependencies
            self.intAdder.writebackVals(wbStation, wbValue)
            self.fpAdder.writebackVals(wbStation, wbValue)
            self.fpMult.writebackVals(wbStation, wbValue)
            # Clear the RS from wherever it originated
            self.intAdder.writebackClear(wbStation)
            self.fpAdder.writebackClear(wbStation)
            self.fpMult.writebackClear(wbStation)
            
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
