# Assembler
import argparse
import re

parser = argparse.ArgumentParser()
parser.add_argument('filename')
args = parser.parse_args()

register = {
        'a': 0,
        'b': 1,
        'c': 2,
        'd': 3,
        'x': 5,
        'spcl': 6,
        'spch': 7
        }

instruction = {
        'stop': 0,
        'ldi': 1, 'ldd': 2, 'ldx': 3, 'std': 4, 'stx': 5,
        'mov':  6,
        'bra': 7, 'bcs': 8, 'bcc': 9, 'beq': 10, 'bne': 11, 'bsr': 12, 'rts': 13,
        'add': 16, 'adc': 17, 'inc': 18, 'and': 19, 'or': 20, 'not': 21, 'xor': 22, 'lsl': 23, 'lsr': 24,
        'dec': 25,
        'clc': 26, 'sec': 27,
        'incx': 28
        }

def tokenise(line):
    """Split a line in to the component parts."""
    l = re.split('\t|,', line)  # split on tabs, comma and space
    l = [a.strip() for a in l]  # remove whitespace from each item
    return list(filter(None, l))  # remove empty strings from list


def parse(tokens):
    """Find the opcode and operands, remove comments."""
    opcode = tokens[0]
    if tokens[-1][0] == ';':
        tokens.pop(-1)
    operands = tokens[1:]
    return opcode, operands


def machine(opcode, operands):
    """Create the machine code from the opcode and operands."""
    if opcode in ['stop', 'rts', 'clc', 'sec', 'incx']:
        return _op(opcode)
    elif opcode in ['ldi', 'ldd', 'std']:
        return _op_reg_abs8(opcode, operands[0], operands[1])
    elif opcode in ['ldx', 'stx']:
        return _op_reg(opcode, operands[0])
    elif opcode == 'mov':
        return _op_reg_reg(opcode, operands[0], operands[1])
    elif opcode in ['bra', 'bcs', 'bcc', 'beq', 'bne', 'bsr']:
        return _op_abs11(opcode, operands[0])
    elif opcode in ['add', 'adc', 'and', 'or', 'xor']:
        return _op_reg_reg_reg(opcode, operands[0], operands[1], operands[2])
    elif opcode in ['not', 'lsl', 'lsr', 'inc', 'dec']:
        return _op_reg_reg(opcode, operands[0], operands[1])
    elif opcode == 'cmp':
        # A compare is the same as an XOR, but in this case we discard the result
        return _op_reg_reg_reg('xor', 'a', operands[0], operands[1], compare=True)
    else:
        return 65535

def _op(opcode):
    return instruction[opcode] << 11

def _op_reg(opcode, R):
    return instruction[opcode] << 11 | register[R] << 8

def _op_reg_reg(opcode, Rd, Rs):
    return instruction[opcode] << 11 | register[Rd] << 8 | register[Rs] << 4

def _op_reg_reg_reg(opcode, Rd, Rs1, Rs2, compare=False):
    m = instruction[opcode] << 11 | register[Rd] << 8 | register[Rs1] << 4 | register[Rs2]
    if compare:
        m = m | (1 << 7)  # if a compare, use bit 7 to tell ALU to discard result
    return m

def _op_reg_abs8(opcode, R, abs):
    abs = int(abs, 0)
    if abs >= 255:
        raise Exception('Absolute value must be less than 255')
    return instruction[opcode] << 11 | register[R] << 8 | abs

def _op_abs11(opcode, abs):
    abs = int(abs, 0)
    if abs >= 2048:
        raise Exception('Absolute value must be less than 2048')
    return instruction[opcode] << 11 | abs


def machine2string(m):
    """Turn the machine code in to a printable string."""
    s = bin(m)[2:]  # strip 0b off the string
    s = s.rjust(16, '0')  # make the bin representation 16 bits
    return s[0:5] + ' ' + s[5:8] + ' ' + s[8:12] + ' ' + s[12:16]  # chunk so easy to read


if __name__ == "__main__":
    with open(args.filename, 'r') as f:
        for line in f.readlines():
            line = line.lstrip().rstrip().lower()
            if len(line) == 0:
                # Empty line
                pass
            elif line[0] == ';':
                # Comments can be skipped
                pass
            elif line[0] == '.':
                # Handle . commands
                # todo
                pass
            else:
                # Assume to be assembly code
                tokens = tokenise(line)
                opcode, operands = parse(tokens)
                m = machine(opcode, operands)
                print(f'{machine2string(m)}\t: {opcode} {operands}')

