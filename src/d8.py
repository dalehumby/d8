"""
D8 Machine Instruction
"""
from lark import Token, Tree

register = {"A": 0, "B": 1, "C": 2, "D": 3, "E": 4, "PAGE": 5, "X": 6, "SP": 7}

instruction = {
    "stop": 0,
    "clr": 1,
    "ldi": 1,
    "ldd": 2,
    "ldx": 3,
    "ldsp": 4,
    "std": 5,
    "stx": 6,
    "stsp": 7,
    "mov": 8,
    "nop": 8,
    "bra": 9,
    "bcs": 10,
    "bcc": 11,
    "beq": 12,
    "bne": 13,
    "bsr": 14,
    "rts": 15,
    "add": 16,
    "adc": 17,
    "rolc": 17,
    "inc": 18,
    "sbb": 19,
    "dec": 20,
    "and": 21,
    "or": 22,
    "xor": 23,
    "not": 24,
    "rorc": 26,
    "clc": 27,
    "sec": 28,
    "psh": 29,
    "pul": 30,
}


# The symbol table expression resolver expects a Tree not an int
ZERO = Tree("integer", [Token("INT", "0")])
ONE = Tree("integer", [Token("INT", "1")])


class Machine:
    def __init__(self, symbol_table):
        self.symbol_table = symbol_table

    def instruction(self, address, opcode, operands):
        """
        Create the machine code from the opcode and operands.
        Some instructions require relative addresses: They need the address of the current command
        """
        # The program counter (PC) has already been incremented by the time the instuction is executed
        PC = address + 2

        if opcode in ["clc", "nop", "sec", "stop"]:
            return self.op(opcode)
        elif opcode == "ldi":
            return self.op_reg_opr8u(opcode, operands[0], operands[1])
        elif opcode == "ldd":
            return self.op_reg_opr8u(opcode, operands[0], operands[1])
        elif opcode == "ldx":
            return self.op_reg_opr8s(opcode, operands[0], operands[1])
        elif opcode == "ldsp":
            return self.op_reg_opr8s(opcode, operands[0], operands[1])
        elif opcode == "std":
            return self.op_reg_opr8u(opcode, operands[0], operands[1])
        elif opcode == "stx":
            return self.op_reg_opr8s(opcode, operands[0], operands[1])
        elif opcode == "stsp":
            return self.op_reg_opr8s(opcode, operands[0], operands[1])
        elif opcode == "mov":
            return self.op_reg_reg(opcode, operands[0], operands[1])
        elif opcode in ["bra", "bcs", "bcc", "beq", "bne", "bsr"]:
            return self.op_opr11s(PC, opcode, operands[0])
        elif opcode in ["add", "adc", "sbb", "and", "or", "xor"]:
            return self.op_reg_reg_reg(opcode, operands[0], operands[1], operands[2])
        elif opcode in ["not", "rorc", "inc", "dec"]:
            if len(operands) == 1:
                # If only 1 register specified then source and destination registers are the same
                operands.append(operands[0])
            return self.op_reg_reg(opcode, operands[0], operands[1])
        elif opcode == "rts":
            # For RTS, the register is ignored, so set to a;
            # and opr8s points to location SP+1 because the SP dec only happens after a pull
            return self.op_reg_opr8s(opcode, "A", ONE)
        elif opcode == "psh":
            # opr8 is 0 because no SP offset
            return self.op_reg_opr8s(opcode, operands[0], ZERO)
        elif opcode == "pul":
            # opr8 points to location SP+1 because the SP dec only happens after a pull
            return self.op_reg_opr8s(opcode, operands[0], ONE)
        elif opcode == "cmp":
            # A compare is the same as an SBB, but in this case we discard the result
            return self.op_reg_reg_reg(
                "sbb", "A", operands[0], operands[1], compare=True
            )
        elif opcode == "clr":
            # Load regiser with 0
            return self.op_reg_opr8s(opcode, operands[0], ZERO)
        elif opcode in ["rolc"]:
            # Rotate left through carry is the same as REG + REG + Carry
            if len(operands) == 1:
                # If only 1 register specified then source and destination registers are the same
                operands.append(operands[0])
            return self.op_reg_reg_reg(opcode, operands[0], operands[1], operands[1])
        else:
            raise Exception(f"Unrecognised opcode {opcode}")

    def op(self, opcode):
        return instruction[opcode] << 11

    def op_reg_reg(self, opcode, Rd, Rs):
        return instruction[opcode] << 11 | register[Rd] << 8 | register[Rs] << 4

    def op_reg_reg_reg(self, opcode, Rd, Rs1, Rs2, compare=False):
        m = (
            instruction[opcode] << 11
            | register[Rd] << 8
            | register[Rs1] << 4
            | register[Rs2]
        )
        if compare:
            m = m | (1 << 7)  # if a compare, use bit 7 to tell ALU to discard result
        return m

    def op_reg_opr8u(self, opcode, R, opr8u):
        """
        Resolve symbol or number to an 8-bit unsigned operand.
        NOTE: Use mod 256 so only the low byte of the address is stored in the operand.
              Programmer must use PAGE register to change high byte
        """
        # If not a token (symbol) then try tree (location)
        opr8u = self.symbol_table.resolve_expression(opr8u) % 256
        return instruction[opcode] << 11 | register[R] << 8 | opr8u

    def op_reg_opr8s(self, opcode, R, offset):
        """Resolve symbol or number to an 8-bit signed operand."""
        offset = self.symbol_table.resolve_expression(offset)
        if offset < -128 or offset > 127:
            raise Exception(f"Offset {offset} must be in range -128 to +127")
        if offset < 0:
            # Two's complement
            opr8s = 2 ** 8 + offset
        else:
            opr8s = offset
        return instruction[opcode] << 11 | register[R] << 8 | opr8s

    def op_opr11s(self, PC, opcode, location):
        """Given an opcode and location symbols, calculate the relative offset address."""
        address = self.symbol_table.resolve_expression(location)
        offset = address - PC
        if offset < -1024 or offset > 1023:
            raise Exception(
                f"Relative address {offset} must be in range -1024 to +1023"
            )
        if offset < 0:
            # Two's complement
            opr11s = 2 ** 11 + offset
        else:
            opr11s = offset
        return instruction[opcode] << 11 | opr11s

    def string(self, bin_instruction):
        """Turn the machine code in to a printable string."""
        s = format(bin_instruction, "016b")
        return (
            s[0:5] + " " + s[5:8] + " " + s[8:12] + " " + s[12:16]
        )  # chunk so easy to read
