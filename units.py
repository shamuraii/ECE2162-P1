from architecture import ReservationStation

class IntAdder:
    def __init__(self, rs_count: int, ex_cycles: int, fu_count: int) -> None:
        self.rs_count = rs_count
        self.ex_cycles = ex_cycles
        self.fu_count = fu_count
        self.rs = []
        for i in range(rs_count):
            self.rs.append(ReservationStation())

    def __str__(self) -> str:
        pass


class FloatAdder:
    def __init__(self) -> None:
        pass

class FloatMult:
    def __init__(self) -> None:
        pass

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

class MemoryUnit:
    def __init__(self) -> None:
        pass
