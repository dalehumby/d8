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
        return op(opcode)
    elif opcode in ['ldi', 'ldd', 'std']:
        return op_reg_abs8(opcode, operands[0], operands[1])
    elif opcode in ['ldx', 'stx']:
        return op_reg(opcode, operands[0])
    elif opcode == 'mov':
        return op_reg_reg(opcode, operands[0], operands[1])
    elif opcode in ['bra', 'bcs', 'bcc', 'beq', 'bne', 'bsr']:
        return op_abs11(opcode, operands[0])
    elif opcode in ['add', 'adc', 'and', 'or', 'xor']:
        return op_reg_reg_reg(opcode, operands[0], operands[1], operands[2])
    elif opcode in ['not', 'lsl', 'lsr', 'inc', 'dec']:
        return op_reg_reg(opcode, operands[0], operands[1])
    elif opcode == 'cmp':
        # A compare is the same as an XOR, but in this case we discard the result
        return op_reg_reg_reg('xor', 'a', operands[0], operands[1], compare=True)
    else:
        return 65535

def op(opcode):
    return instruction[opcode] << 11

def op_reg(opcode, R):
    return instruction[opcode] << 11 | register[R] << 8

def op_reg_reg(opcode, Rd, Rs):
    return instruction[opcode] << 11 | register[Rd] << 8 | register[Rs] << 4

def op_reg_reg_reg(opcode, Rd, Rs1, Rs2, compare=False):
    m = instruction[opcode] << 11 | register[Rd] << 8 | register[Rs1] << 4 | register[Rs2]
    if compare:
        m = m | (1 << 7)  # if a compare, use bit 7 to tell ALU to discard result
    return m


def resolve_symbol(s):
    try:
        return int(str(s), 0)
    except ValueError:
        try:
            return resolve_symbol(symbol[s])
        except KeyError:
            raise Exception(f"Undefined symbol '{s}'")

def op_reg_abs8(opcode, R, abs):
    abs = resolve_symbol(abs)
    if abs >= 255:
        raise Exception('Absolute value must be less than 255')
    return instruction[opcode] << 11 | register[R] << 8 | abs

def op_abs11(opcode, abs):
    abs = resolve_symbol(abs)
    if abs >= 2048:
        raise Exception('Absolute value must be less than 2048')
    return instruction[opcode] << 11 | abs


def machine2string(m):
    """Turn the machine code in to a printable string."""
    s = format(m, '016b')
    return s[0:5] + ' ' + s[5:8] + ' ' + s[8:12] + ' ' + s[12:16]  # chunk so easy to read


if __name__ == "__main__":
    symbol = {}
    address = 0

    with open(args.filename, 'r') as f:
        for line in f.readlines():
            line = line.lstrip().rstrip().lower()
            if not line:
                # Empty line
                pass
            elif line[0] == ';':
                # Comments can be skipped
                pass
            elif line[0] == '.':
                define = re.search(r"\.define\s+(\w+)\s+(\w+)", line)
                data = re.search(r"\.data\s+(\w+)\s+(\w+)(?:$|\s+\{(.*)\})", line)
                if define:
                    groups = define.groups()
                    symbol[groups[0]] = groups[1]
                elif data:
                    groups = data.groups()
                    symbl = groups[0]
                    symbol[symbl] = address
                    byte_count = resolve_symbol(groups[1])
                    print(f'{format(address, "04x")} : {symbl}[{byte_count}]')
                    address += byte_count
                    values = groups[2]
                    if values:
                        v = values.split(',')
                        v = [int(y) for y in v]
                else:
                    raise Exception(f'Cannot parse line {line}')
            else:
                # Assume to be assembly code
                tokens = tokenise(line)
                opcode, operands = parse(tokens)
                m = machine(opcode, operands)
                print(f'{format(address, "04x")} : {machine2string(m)}\t| {opcode} {operands}')
                address += 2

    print(symbol)
