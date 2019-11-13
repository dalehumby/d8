# D8 Assembler
# Basic 2-pass assembler.
#
# Case insensitive
# Defines and then data then code
# Defines and Data only support back references
# Code supports forward and back references
#

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


def resolve_symbol(symbol):
    address = 0
    if type(symbol) == int:
        return symbol
    for s in symbol.split('+'):
        try:
            address += int(str(s), 0)
        except ValueError:
            s = s.strip('&')  # Use the & symbol to refer to an address for readability, but not needed by assembler
            try:
                address += resolve_symbol(symbols[s])
            except KeyError:
                raise Exception(f"Undefined symbol '{s}'")
    return address

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
    symbols = {}
    address = 0
    memory = {}

    with open(args.filename, 'r') as f:
        for line in f.readlines():
            line = line.split(';')[0]  # remove comments
            line = line.strip().lower()  # remove leading and trailing whitespace, and lowercase
            if not line:
                # Empty line skipped
                pass
            elif line[0] == ';':
                # Comments can be skipped
                pass
            elif line[0] == '.':
                # Handle . command
                define = re.search(r"\.define\s+(\w+)\s+(\w+)", line)
                reset = re.search(r"\.reset\s+(\w+)", line)
                origin = re.search(r"\.origin\s+(\w+)", line)
                data = re.search(r"\.data\s+(\w+)\s+(\w+)(?:\s*\{(.*)\})?", line)
                if define:
                    groups = define.groups()
                    symbols[groups[0]] = groups[1]
                elif reset:
                    # Create the reset command in first 2 bytes of RAM
                    reset_address = reset.groups()[0]
                    address = 0
                    memory[address] = {'type': 'instruction', 'op': 'bra', 'opr': [reset_address]}
                    address += 2
                elif origin:
                    # Change the address to the origin
                    origin = origin.groups()[0]
                    address = resolve_symbol(origin)
                elif data:
                    groups = data.groups()
                    smbl = groups[0]
                    if smbl in symbols:
                        raise Exception(f'Symbol "{smbl}" already defined')
                    symbols[smbl] = address
                    memory[address] = {'type': 'symbol', 'symbol': smbl}
                    byte_count = resolve_symbol(groups[1])
                    print(f'{format(address, "04x")} : {smbl}[{byte_count}]')
                    address += byte_count
                    values = groups[2]
                    if values:
                        v = values.split(',')
                        v = [int(y) for y in v]
                else:
                    #raise Exception(f'Cannot parse line {line}')
                    pass
            elif line[-1] == ':':
                # Handle location symbol
                tokens = line.split()
                smbl = tokens[0][:-1]
                if smbl in symbols:
                    raise Exception(f'Symbol "{smbl}" already defined')
                symbols[smbl] = address
                memory[address] = {'type': 'symbol', 'symbol': smbl}
                print(f'{format(address, "04x")} : {smbl}')
            else:
                # Assume to be assembly code
                tokens = tokenise(line)
                opcode, operands = parse(tokens)
                memory[address] = {'type': 'instruction', 'op': opcode, 'opr': operands}
                address += 2

    print(symbols)

    for address, line in memory.items():
        if line['type'] == 'instruction':
            opcode = line['op']
            operands = line['opr']
            m = machine(opcode, operands)
            print(f'{format(address, "04x")} : {machine2string(m)}\t| {opcode} {operands}')
        else:
            print(f'{format(address, "04x")} : {line["symbol"]}')

        # todo: print branch symbols in amongst the code
        # todo: nice to have: print how assembler resolved the symbol
