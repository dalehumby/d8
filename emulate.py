# D8 Emulator

import re

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

class Emulator:
    def __init__(self, filename):
        self.memory, self.line_map, self.variables = self._load_d8_file(filename)
        self.reset()

    def reset(self):
        self.pc = 0
        self.status = {
            'zero': False,
            'carry': False,
            'stop': False
            }
        self.registers = [0] * 8
        self.ir = 0

    def step(self):
        """Step the CPU by 1 instruction."""
        if not self.status['stop']:
            self._fetch()
            opcode, operands = self._decode()
            self._execute(opcode, operands)

    def display_source(self, source):
        line_number = self.line_map[self.pc]
        source_line = source[line_number-1]
        print(f'{line_number} : {source_line}')

    def display_variables(self):
        """Display all the variables and their content."""
        print(f'Stauts: {self.status}')
        print(f'Registers: {self.registers}\tPC: 0x{format(self.pc, "04x")}')
        for name, v in self.variables.items():
            content = [ self.memory[adr] for adr in range(v['address'], v['address'] + v['length']) ]
            print(f'{name}[{v["length"]}]: {content}')

    def _load_d8_file(self, filename):
        """Load the .d8 file in to memory."""
        memory = {}
        line_map = {}
        variables = {}
        with open(filename, 'r') as f:
            for line in f.readlines():
                mem, line_number, variable = self._parseline(line)
                if mem:
                    memory.update(mem)
                if line_number:
                    line_map.update(line_number)
                if variable:
                    variables.update(variable)
        return memory, line_map, variables

    def load_source(self, filename):
        """
        Load the original source .asm file
        Returns a list of lines that you can index in to
        """
        filename = filename.split('.')[0] + '.asm'
        with open(filename, 'r') as f:
            lines = f.readlines()
        lines = [ line.strip() for line in lines ]
        return lines

    def _parseline(self, line):
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

    def _fetch(self):
        """
        Fetch an instruction from memory, load it in to the instruction register (ir)
        Increment the program counter (pc)
        """
        self.ir = self.memory[self.pc] << 8  # Load high byte of instruction register
        self.pc += 1
        self.ir |= self.memory[self.pc]  # Load the low byte
        self.pc += 1

    def _decode(self):
        """
        Decode the instruction register (ir) in to the opcode and operations.
        Map the integer opcode to the text instruction.
        """
        opcode =   (self.ir & 0b1111100000000000) >> 11
        operands = self.ir & 0b0000011111111111
        opcode = instruction_map[opcode]
        return opcode, operands

    def _get_reg(self, operands):
        """Get 1 register."""
        R = operands >> 8
        return R

    def _get_reg_reg(self, operands):
        """Get 2 registers."""
        Rd = operands >> 8
        Rs = (operands & 0b01110000) >> 4
        return Rd, Rs

    def _get_reg_reg_reg(self, operands):
        """Get 3 registers."""
        Rd = operands >> 8
        Rs1 = (operands & 0b01110000) >> 4
        Rs2 = operands & 0b00000111
        if Rd in [Rs1, Rs2]:
            # Limitation of the CPU is you cannot save data in to the same register
            # as the one you are reading from
            raise Exception('Source register cannot also be destination register')
        return Rd, Rs1, Rs2

    def _get_reg_abs8(self, operands):
        """Get 1 register and an 8-bit value."""
        Rd = operands >> 8
        abs8 = operands & 0xFF
        return Rd, abs8

    def _get_abs11(self, operands):
        """Get an 11-bit value."""
        abs11 = operands
        return abs11

    def _execute(self, opc, opr):
        """Execute the current opcode."""
        #print(f'Execute: {opc}\t 0b{format(opr, "011b")}({opr})')

        if opc == 'stop':
            self.status['stop'] = True
        elif opc == 'ldi':
           Rd, data = self._get_reg_abs8(opr)
           self.registers[Rd] = data
           #print(f'{map_num_reg[Rd]}<-{data}')
        elif opc == 'ldd':
           Rd, address = self._get_reg_abs8(opr)
           data = self.memory[address]
           self.registers[Rd] = data
           #print(f'{map_num_reg[Rd]}<-{data}<-memory[{address}]')
        elif opc == 'ldx':
            Rd = self._get_reg(opr)
            address = self.registers[map_reg_num['X']]
            data = self.memory[address]
            self.registers[Rd] = data
            #print(f'{map_num_reg[Rd]}<-{data}<-memory[X={address}]')
        elif opc == 'std':
            Rs, address = self._get_reg_abs8(opr)
            data = self.registers[Rs]
            self.memory[address] = data
            #print(f'memory[{address}]<-{data}<-{map_num_reg[Rs]}')
        elif opc == 'stx':
            Rs = self._get_reg(opr)
            data = self.registers[Rs]
            address = self.registers[map_reg_num['X']]
            self.memory[address] = data
            #print(f'memory[{address}]<-{data}<-{map_num_reg[Rs]}')
        elif opc == 'mov':
            Rd, Rs = self._get_reg_reg(opr)
            data = self.registers[Rs]
            self.registers[Rd] = data
            #print(f'{map_num_reg[Rd]}<-{data}<-{map_num_reg[Rs]}')
        elif opc == 'bra':
            self.pc = self._get_abs11(opr)
        elif opc == 'beq':
            if self.status['zero']:
                self.pc = self._get_abs11(opr)
        elif opc == 'bne':
            if not self.status['zero']:
                self.pc = self._get_abs11(opr)
        elif opc == 'bcs':
            if self.status['carry']:
                self.pc = self._get_abs11(opr)
        elif opc == 'bcc':
            if not self.status['carry']:
                self.pc = self._get_abs11(opr)
        elif opc == 'bsr':
            # Save the program counter in the shaddow program counter (SPC) registers
            # Each register is only 8 bits, so split the 16-bit PC in to a high and low byte
            self.registers[map_reg_num['SPCH']] = self.pc >> 8
            self.registers[map_reg_num['SPCL']] = self.pc & 0xFF
            self.pc = self._get_abs11(opr)
        elif opc == 'rts':
            # To return from subroutine, copy the shaddow program counter in to the program counter
            self.pc = self.registers[map_reg_num['SPCH']] << 8 | self.registers[map_reg_num['SPCL']]
        elif opc in ['add', 'adc', 'inc', 'and', 'or', 'not', 'xor', 'lsl', 'lsr', 'dec']:
            self._alu(opc, opr)
        elif opc in ['clc', 'sec']:
            self.status['carry'] = (opc == 'sec')
        elif opc == 'incx':
            self.registers[map_reg_num['X']] += 1
        else:
            #print(self.status)
            #print(self.registers)
            raise Exception('Unrecognised opcode {opc}')


    def _alu(self, opcode, operands):
        """Emulate the ALU execution cycles."""

        def _full_add(Rs1, Rs2, carry):
            """Implement the full adder."""
            Rd = Rs1 + Rs2 + carry
            carry = Rd > 0xFF
            Rd &= 0xFF  # Ensure result in range 0 to 0xFF
            return Rd, carry

        Rd, Rs1, Rs2 = self._get_reg_reg_reg(operands)

        if opcode == 'add':
            data, self.status['carry'] = _full_add(self.registers[Rs1], self.registers[Rs2], 0)
        elif opcode == 'adc':
            data, self.status['carry'] = _full_add(self.registers[Rs1], self.registers[Rs2], self.status['carry'])
        elif opcode == 'inc':
            data, self.status['carry'] = _full_add(self.registers[Rs1], 0, 1)
        elif opcode == 'dec':
            data, self.status['carry'] = _full_add(self.registers[Rs1], 0xFF, 0)
        elif opcode == 'and':
            data = self.registers[Rs1] & self.registers[Rs2]
        elif opcode == 'or':
            data = self.registers[Rs1] | self.registers[Rs2]
        elif opcode == 'xor':
            data = self.registers[Rs1] ^ self.registers[Rs2]
        elif opcode == 'not':
            data = ~self.registers[Rs1]
        elif opcode == 'lsl':
            pass
        elif opcode == 'lsr':
            pass

        # Set the status bits
        self.status['zero'] = data == 0

        # If bit 7 is clear then save the result
        if operands & 0b10000000 == 0:
            self.registers[Rd] = data


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('filename', help='.d8 file to load in to emulator')
    args = parser.parse_args()

    d8 = Emulator(args.filename)
    source = d8.load_source(args.filename)

    while not d8.status['stop']:
        d8.display_source(source)
        d8.step()
        d8.display_variables()
        input()

