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

class IntRegisters:
    def __init__(self) -> None:
        pass

class FloatRegisters:
    def __init__(self) -> None:
        pass

class MemoryUnit:
    def __init__(self) -> None:
        pass
