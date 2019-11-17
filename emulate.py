# D8 Emulator (non-GUI version)

import re
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('filename')
args = parser.parse_args()

map_reg_num = {
        'a': 0,
        'b': 1,
        'c': 2,
        'd': 3,
        'x': 5,
        'spcl': 6,
        'spch': 7
        }
map_reg_num = { key.upper(): value for key, value in map_reg_num.items() }  # uppercase the keys
map_num_reg = { value: key.upper() for key, value in map_reg_num.items() }  # invert the dictionary

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

instruction_map = {value: key for key, value in instruction.items() }


def parseline(line):
    """
    Given a line in d8 format, return a dictionary with the key as the address
    and the value as a tuple of (memory contents, line number, variable)
    """
    if line.startswith(';'):
        # Skip comment lines
        return None, None, None
    else:
        line = line.split('|')
        address = int(line[0].strip(), 16)
        value = line[1].strip(' \t')
        line_number = int(line[2].strip(), 10)
        if '[' in value:
            # Handle variables
            memory = {}
            result = re.search(r'(\w+)\[(\d+)\]', value)
            name = result.groups()[0]
            length = int(result.groups()[1], 10)
            for adr in range(address, address+length):
                memory[adr] = 0
            return memory, None, {name: {'length': length, 'address': address}}
        elif value[0] in ['0', '1']:
            value = value.replace(' ', '')  # remove whitespace
            high_byte = int(value[0:8], 2)
            low_byte = int(value[8:], 2)
            return {address: high_byte, address+1: low_byte}, {address: line_number}, None
        else:
            return None, None, None


def load_file(filename):
    """
    Load the .d8 memory file
    """
    memory = {}
    line_map = {}
    variables = {}
    with open(filename, 'r') as f:
        for line in f.readlines():
            mem, line_number, variable = parseline(line)
            if mem:
                memory.update(mem)
            if line_number:
                line_map.update(line_number)
            if variable:
                variables.update(variable)
    return memory, line_map, variables


def load_source(filename):
    """
    Load the original source .asm file
    Returns a list of lines that you can index in to
    """
    filename = filename.split('.')[0] + '.asm'
    with open(filename, 'r') as f:
        lines = f.readlines()
    lines = [ line.strip() for line in lines ]
    return lines


def display_source(pc, line_map, source):
    line_number = line_map[pc]
    source_line = source[line_number-1]
    print(f'{line_number} : {source_line}')


def display_variables(variables):
    """Display all the variables and their content."""
    for name, v in variables.items():
        content = [ memory[adr] for adr in range(v['address'], v['address'] + v['length']) ]
        print(f'{name}[{v["length"]}]: {content}')


def fetch():
    """
    Fetch an instruction from memory, load it in to the instruction register (ir)
    Increment the program counter (pc)
    """
    global pc, ir
    ir = memory[pc] << 8  # Load high byte of instruction register
    pc += 1
    ir |= memory[pc]  # Load the low byte
    pc += 1


def decode():
    opcode =   (ir & 0b1111100000000000) >> 11
    operands = ir & 0b0000011111111111
    opcode = instruction_map[opcode]
    return opcode, operands

def get_reg(operands):
    R = operands >> 8
    return R

def get_reg_reg(operands):
    Rd = operands >> 8
    Rs = (operands & 0b01110000) >> 4
    return Rd, Rs

def get_reg_reg_reg(operands):
    Rd = operands >> 8
    Rs1 = (operands & 0b01110000) >> 4
    Rs2 = operands & 0b00000111
    if Rd in [Rs1, Rs2]:
        # Limitation of the CPU is you cannot save data in to the same register
        # as the one you are reading from
        raise Exception('Source register cannot also be destination register')
    return Rd, Rs1, Rs2

def get_reg_abs8(operands):
    Rd = operands >> 8
    abs8 = operands & 0xFF
    return Rd, abs8

def get_abs11(operands):
    abs11 = operands
    return abs11

def execute(opc, opr):
    """Ececute the current opcode."""
    global pc, status, registers
    print(f'Execute: {opc}\t {format(opr, "011b")}({opr})')

    if opc == 'stop':
        status['stop'] = True
    elif opc == 'ldi':
       Rd, data = get_reg_abs8(opr)
       registers[Rd] = data
       print(f'{map_num_reg[Rd]}<-{data}')
    elif opc == 'ldd':
       Rd, address = get_reg_abs8(opr)
       data = memory[address]
       registers[Rd] = data
       print(f'{map_num_reg[Rd]}<-{data}<-memory[{address}]')
    elif opc == 'ldx':
        Rd = get_reg(opr)
        address = registers[map_reg_num['X']]
        data = memory[address]
        registers[Rd] = data
        print(f'{map_num_reg[Rd]}<-{data}<-memory[X={address}]')
    elif opc == 'std':
        Rs, address = get_reg_abs8(opr)
        data = registers[Rs]
        memory[address] = data
        print(f'memory[{address}]<-{data}<-{map_num_reg[Rs]}')
    elif opc == 'stx':
        Rs = get_reg(opr)
        data = registers[Rs]
        address = registers[map_reg_num['X']]
        memory[address] = data
        print(f'memory[{address}]<-{data}<-{map_num_reg[Rs]}')
    elif opc == 'mov':
        Rd, Rs = get_reg_reg(opr)
        data = registers[Rs]
        registers[Rd] = data
        print(f'{map_num_reg[Rd]}<-{data}<-{map_num_reg[Rs]}')
    elif opc == 'bra':
        pc = get_abs11(opr)
    elif opc == 'beq':
        if status['zero']:
            pc = get_abs11(opr)
    elif opc == 'bne':
        if not status['zero']:
            pc = get_abs11(opr)
    elif opc == 'bcs':
        if status['carry']:
            pc = get_abs11(opr)
    elif opc == 'bcc':
        if not status['carry']:
            pc = get_abs11(opr)
    elif opc == 'bsr':
        # Save the program counter in the shaddow program counter (SPC) registers
        # Each register is only 8 bits, so split the 16-bit PC in to a high and low byte
        registers[map_reg_num['SPCH']] = pc >> 8
        registers[map_reg_num['SPCL']] = pc & 0xFF
        pc = get_abs11(opr)
    elif opc == 'rts':
        # To return from subroutine, copy the shaddow program counter in to the program counter
        pc = registers[map_reg_num['SPCH']] << 8 | registers[map_reg_num['SPCL']]
    elif opc in ['add', 'adc', 'inc', 'and', 'or', 'not', 'xor', 'lsl', 'lsr', 'dec']:
        alu(opc, opr)
    elif opc in ['clc', 'sec']:
        status['carry'] = (opc == 'sec')
    elif opc == 'incx':
        registers[map_reg_num['X']] += 1
    else:
        print(status)
        print(registers)
        raise Exception(f'Unrecognised opcode {opc}')


def alu(opcode, operands):
    """Emulate the ALU execution cycles."""
    global registers

    def _full_add(Rs1, Rs2, carry):
        """Implement the full adder."""
        Rd = Rs1 + Rs2 + carry
        carry = Rd > 0xFF
        Rd &= 0xFF  # Ensure result in range 0 to 0xFF
        return Rd, carry

    Rd, Rs1, Rs2 = get_reg_reg_reg(operands)

    if opcode == 'add':
        data, status['carry'] = _full_add(registers[Rs1], registers[Rs2], 0)
    elif opcode == 'adc':
        data, status['carry'] = _full_add(registers[Rs1], registers[Rs2], status['carry'])
    elif opcode == 'inc':
        data, status['carry'] = _full_add(registers[Rs1], 0, 1)
    elif opcode == 'dec':
        data, status['carry'] = _full_add(registers[Rs1], 0xFF, 0)
    elif opcode == 'and':
        data = registers[Rs1] & registers[Rs2]
    elif opcode == 'or':
        data = registers[Rs1] | registers[Rs2]
    elif opcode == 'xor':
        data = registers[Rs1] ^ registers[Rs2]
    elif opcode == 'not':
        data = ~registers[Rs1]
    elif opcode == 'lsl':
        pass
    elif opcode == 'lsr':
        pass

    # Set the status bits
    status['zero'] = data == 0

    # If bit 7 is clear then save the result
    if operands & 0b10000000 == 0:
        registers[Rd] = data


if __name__ == "__main__":
    # First load the d8 file in to memory
    memory, line_map, variables = load_file(args.filename)
    source = load_source(args.filename)
    #print('Memory: ', memory)
    #print('Line numbers: ' , line_map)

    # On CPU reset, initialise the system
    pc = 0
    status = {
        'zero': False,
        'carry': False,
        'stop': False
        }
    registers = [0] * 8
    ir = 0

    while not status['stop']:
        display_source(pc, line_map, source)
        fetch()
        opcode, operands = decode()
        execute(opcode, operands)
        # Store is part of the execute function
        print(f'Stauts: {status}')
        print(f'Registers: {registers}')
        display_variables(variables)
        input()
