"""
D8 Assembler
Basic 2-pass assembler.

Notes:
- Case insensitive

Output format:
.asm file
Address (hex) | Contents of address (multiple bytes fine) (hex) | line number | debug info

Debug info section is freeform text.
Supports var:varname[byte length (base 10 integer)] to tell emulator that there is a variable at that location

"""

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
        'e': 4,
        'page': 5,
        'x': 6,
        'sp': 7
        }

instruction = {
        'stop': 0,
        'ldi': 1, 'ldd': 2, 'ldx': 3, 'ldsp': 4, 'std': 5, 'stx': 6, 'stsp': 7,
        'mov':  8,
        'bra': 9, 'bcs': 10, 'bcc': 11, 'beq': 12, 'bne': 13, 'bsr': 14, 'rts': 15,
        'add': 16, 'adc': 17, 'inc': 18, 'dec': 19, 'and': 20, 'or': 21, 'xor': 22, 'not': 23, 'rolc': 24, 'rorc': 25,
        'clc': 26, 'sec': 27,
        'psh': 28, 'pul': 29
        }


def tokenise(line):
    """Split a line in to the component parts."""
    return re.split(r'[^A-Za-z0-9_+]+', line)  # split on any character that is not (^) in that list []


def parse(tokens):
    """Find the opcode and operands, remove comments."""
    opcode = tokens[0]
    if tokens[-1][0] == ';':
        tokens.pop(-1)
    operands = tokens[1:]
    return opcode, operands


def machine(address, opcode, operands):
    """
    Create the machine code from the opcode and operands.
    Some instructions require relative addresses: They need the address of the current command
    """
    PC = address + 2  # The program counter (PC) has already been incremented by the time the instuction is executed

    if opcode in ['stop', 'clc', 'sec']:
        return op(opcode)
    elif opcode in ['ldi', 'ldd', 'std']:
        return op_reg_opr8u(opcode, operands[0], operands[1])
    elif opcode in ['ldx', 'ldsp', 'stx', 'stsp']:
        return op_reg_opr8s(opcode, operands[0], operands[1])
    elif opcode == 'mov':
        return op_reg_reg(opcode, operands[0], operands[1])
    elif opcode in ['bra', 'bcs', 'bcc', 'beq', 'bne', 'bsr']:
        return op_opr11s(PC, opcode, operands[0])
    elif opcode in ['add', 'adc', 'and', 'or', 'xor']:
        return op_reg_reg_reg(opcode, operands[0], operands[1], operands[2])
    elif opcode in ['not', 'rolc', 'rorc', 'inc', 'dec']:
        return op_reg_reg(opcode, operands[0], operands[1])
    elif opcode == 'rts':
        # For RTS, the register is ignored, so set to a; and opr8 points to location SP+1 because the SP dec only happens after a pull
        return op_reg_opr8s(opcode, 'a', 1)
    elif opcode == 'psh':
        # opr8 is 0 because no SP offset
        return op_reg_opr8s(opcode, operands[0], 0)
    elif opcode == 'pul':
        # opr8 points to location SP+1 because the SP dec only happens after a pull
        return op_reg_opr8s(opcode, operands[0], 1)
    elif opcode == 'cmp':
        # A compare is the same as an XOR, but in this case we discard the result
        return op_reg_reg_reg('xor', 'a', operands[0], operands[1], compare=True)
    else:
        raise Exception(f'Unrecognised opcode {opcode}')


def op(opcode):
    return instruction[opcode] << 11


def op_reg_reg(opcode, Rd, Rs):
    return instruction[opcode] << 11 | register[Rd] << 8 | register[Rs] << 4


def op_reg_reg_reg(opcode, Rd, Rs1, Rs2, compare=False):
    m = instruction[opcode] << 11 | register[Rd] << 8 | register[Rs1] << 4 | register[Rs2]
    if compare:
        m = m | (1 << 7)  # if a compare, use bit 7 to tell ALU to discard result
    return m


def resolve_symbol(symbol):
    """Recursivley resolve symbol references until end up with an address."""
    address = 0
    if type(symbol) == int:
        return symbol
    for s in symbol.split('+'):
        try:
            address += int(str(s), 0)
        except ValueError:
            s = s.strip('& ')  # Use the & symbol to refer to an address for readability, but not needed by assembler. Also strip spaces
            try:
                address += resolve_symbol(symbols[s])
            except KeyError:
                raise Exception(f"Undefined symbol '{s}'")
    return address


def op_reg_opr8u(opcode, R, opr8u):
    """
    Resolve symbol or number to an 8-bit unsigned operand.
    NOTE: Use mod 256 so only the low byte of the address is stored in the operand.
          Programmer must use PAGE register to change high byte
    """
    opr8u = resolve_symbol(opr8u) % 256
    return instruction[opcode] << 11 | register[R] << 8 | opr8u


def op_reg_opr8s(opcode, R, offset):
    """Resolve symbol or number to an 8-bit signed operand."""
    offset = resolve_symbol(offset)
    if offset < -128 or offset > 127:
        raise Exception(f'Offset {offset} must be in range -128 to +127')
    if offset < 0:
        # Two's complement
        opr8s = 2**8 + offset
    else:
        opr8s = offset
    return instruction[opcode] << 11 | register[R] << 8 | opr8s


def op_opr11s(PC, opcode, address):
    """Given an opcode and absolute address, calculate the relative offset."""
    address = resolve_symbol(address)
    offset = address - PC
    if offset < -1024 or offset > 1023:
        raise Exception(f'Relative address {offset} must be in range -1024 to +1023')
    if offset < 0:
        # Two's complement
        opr11s = 2**11 + offset
    else:
        opr11s = offset
    return instruction[opcode] << 11 | opr11s


def machine2string(m):
    """Turn the machine code in to a printable string."""
    s = format(m, '016b')
    return s[0:5] + ' ' + s[5:8] + ' ' + s[8:12] + ' ' + s[12:16]  # chunk so easy to read


if __name__ == "__main__":
    symbols = {}
    address = 0
    memory = {}
    filename = args.filename
    outlines = []

    # First pass of assembler: build the symbol table
    with open(filename, 'r') as f:


        lines = f.readlines()
        for line_number, line in enumerate(lines, start=1):
            line = line.split(';')[0]  # remove comments
            line = line.strip().lower()  # remove leading and trailing whitespace; and lowercase
            if not line or line[0] == ';':
                # Empty line and comments can be skipped
                pass
            elif line[0] == '.':
                # Handle . command
                define = re.search(r"\.define\s+(\w+)\s+(\w+)", line)
                reset = re.search(r"\.reset\s+(\w+)", line)
                origin = re.search(r"\.origin\s+([a-zA-Z0-9+ ]+)", line)
                data = re.search(r"\.data\s+(\w+)\s+(\w+)(?:\s*\"(.*)\")?", line)
                if define:
                    # Define a constant: .define LENGTH 3
                    groups = define.groups()
                    symbols[groups[0]] = groups[1]
                elif reset:
                    # Create the reset command in first 2 bytes of RAM: .reset Start
                    reset_address = reset.groups()[0]
                    address = 0
                    memory[address] = {'type': 'instruction', 'op': 'bra', 'opr': [reset_address], 'line_number': line_number}
                    address += 2
                elif origin:
                    # Change the address to the origin: .origin 0x0100 or .origin Start
                    origin = origin.groups()[0]
                    address = resolve_symbol(origin)
                elif data:
                    # Variable definition: .data i 1 or .data name 10 "value"
                    groups = data.groups()
                    smbl = groups[0]
                    byte_count = resolve_symbol(groups[1])
                    values = groups[2]
                    v = [ 0 ] * byte_count  # init all bytes to 0
                    if values:
                        values = [ ord(x) for x in values ]
                        v[:len(values)] = values
                    if smbl in symbols:
                        raise Exception(f'Symbol "{smbl}" already defined')
                    symbols[smbl] = address
                    memory[address] = {'type': 'variable', 'symbol': smbl, 'value': v, 'line_number': line_number}
                    address += byte_count
                else:
                    raise Exception(f'Cannot parse line {line}')
            elif line[-1] == ':':
                # Add location to the symbol table
                smbl = line[:-1]
                if smbl in symbols:
                    raise Exception(f'Symbol "{smbl}" already defined')
                symbols[smbl] = address
            else:
                # Assume to be assembly code
                tokens = tokenise(line)
                opcode, operands = parse(tokens)
                memory[address] = {'type': 'instruction', 'op': opcode, 'opr': operands, 'line_number': line_number}
                address += 2

    # Write the header of the .d8 file
    out = f'; Assembled {filename}\n; Symbol table = {symbols}\n;Adr | Val  | Ln | Debug info'
    outlines.append(out)
    print(out)

    # Now that we have the complete symbol table, do the second pass
    for address, line in memory.items():
        line_number = line['line_number']
        if line['type'] == 'instruction':
            opcode = line['op']
            operands = line['opr']
            m = machine(address, opcode, operands)
            out = f'{address:04X} | {m:04X} | {line_number:2d} | {opcode} {operands} ({machine2string(m)})'
            outlines.append(out)
            print(out)
        elif line['type'] == 'variable':
            hexstr = ''.join(f'{v:02X}' for v in line['value'])
            out = f'{address:04X} | {hexstr} | {line_number:2d} | var:{line["symbol"]}[{len(line["value"])}]'
            outlines.append(out)
            print(out)
        else:
            raise Exception(f"Unknown type {line['type']}")

    # Write the .d8 file
    outfile = filename.rsplit('.')[0] + '.d8'
    with open(outfile, 'w') as f:
        f.writelines(map(lambda s: s + '\n', outlines))

    # Output the .hex file to be loaded in to RAM of Digital
    max_memory = max(memory)
    if memory[max_memory]['type'] == 'variable':
        max_memory += len(memory[max_memory]['value'])
    else:
        max_memory += 2  # For the two bytes of the instruction
    hex = [0] * max_memory

    for address, line in memory.items():
        if line['type'] == 'instruction':
            m = machine(address, line['op'], line['opr'])
            hex[address] = m >> 8
            hex[address + 1] = m & 0xFF
        elif line['type'] == 'variable':
            for offset, value in enumerate(line['value']):
                hex[address+offset] = value
        else:
            raise Exception(f'Unknown type {line["type"]}')

    outfile = filename.rsplit('.')[0] + '.hex'
    with open(outfile, 'w') as f:
        f.write('v2.0 raw\n')
        f.writelines(map(lambda s: f'{s:02X}\n', hex))
