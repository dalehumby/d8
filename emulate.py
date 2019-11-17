# D8 Emulator (non-GUI version)

import re
import argparse

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

register_map = { value: key.upper() for key, value in register.items() }
instruction_map = {value: key for key, value in instruction.items() }


def parseline(line):
    """
    Given a line in d8 format, return a dictionary with the key as the address
    and the value as a tuple of memory contents and line number
    """
    if line.startswith(';'):
        # Skip comment lines
        return None, None
    else:
        line = line.split('|')
        address = int(line[0].strip(), 16)
        value = line[1].strip(' \t')
        line_number = int(line[2].strip(), 10)
        if '[' in value:
            # Handle variables
            memory = {}
            result = re.search(r'\w+\[(\d+)\]', value)
            length = int(result.groups()[0], 10)
            for adr in range(address, address+length):
                memory[adr] = 0
            return memory, None
        elif value[0] in ['0', '1']:
            value = value.replace(' ', '')  # remove whitespace
            high_byte = int(value[0:8], 2)
            low_byte = int(value[8:], 2)
            return {address: high_byte, address+1: low_byte}, {address: line_number}
        else:
            return None, None


def load_file(filename):
    """
    Load the .d8 memory file
    """
    memory = {}
    line_map = {}
    with open(filename, 'r') as f:
        for line in f.readlines():
            mem, line_number = parseline(line)
            if mem:
                memory.update(mem)
            if line_number:
                line_map.update(line_number)
    return memory, line_map


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


def execute(opc, opr):
    global pc, status, registers
    print(f'Execute: {opc}\t {format(opr, "011b")}({opr})')

    if opc == 'stop':
        status['stop'] = True
    elif opc == 'ldi':
       pass
    elif opc == 'bra':
        pc = opr


def store():
    pass



if __name__ == "__main__":
    # First load the file in to memory
    memory, line_map = load_file(args.filename)
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
        fetch()
        opcode, operands = decode()
        execute(opcode, operands)
        store()

