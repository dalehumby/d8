# D8 Emulator
import os
import queue
import re
import socket
import threading
from textwrap import wrap

from d8 import instruction
from d8 import register as map_reg_num

map_num_reg = {
    value: key.upper() for key, value in map_reg_num.items()
}  # invert the dictionary

instruction_map = {value: key for key, value in instruction.items()}

# Memory locations of the peripherals
periph_map = {"SPPS": 2, "TERM": 3, "KBD": 4}

stop_threads = False


def terminal(screen_q, keyboard_q):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 6543))
        s.listen()
        s.settimeout(0.1)
        while not stop_threads:
            try:
                conn, addr = s.accept()
            except socket.timeout:
                continue
            with conn:
                # print("Connection from:", addr)
                conn.settimeout(0.1)
                while not stop_threads:
                    try:
                        keystrokes = conn.recv(100)
                        for key in keystrokes:  # TODO may need .decode() ?
                            if isinstance(key, str):
                                key = ord(key)
                            keyboard_q.put(key)
                    except socket.timeout:
                        pass

                    try:
                        screen_char = screen_q.get(block=False)
                        if screen_char:
                            conn.sendall(chr(screen_char).encode())
                    except queue.Empty:
                        pass
                conn.close()


class Screen:
    """Screen peripheral handler."""

    def __init__(self, screen_q):
        self.screen_q = screen_q
        self.value = 0

    def read(self):
        return self.value

    def write(self, value):
        self.value = value
        self.screen_q.put(value)


class Keyboard:
    """Keyboard peripheral handler."""

    def __init__(self, keyboard_q):
        self.keyboard_q = keyboard_q
        self.key = 0

    def read(self):
        try:
            self.key = self.keyboard_q.get(block=False)
        except queue.Empty:
            self.key = 0
        return self.key

    def write(self, value):
        # Writes to keyboad are ignored
        pass


class Memory(dict):
    """Read and write to memory, calling out to memory mapped peripherals as needed."""

    def __init__(self, screen_q, keyboard_q):
        """Initialise an empty memory and the peripherals."""
        dict.__init__(self, {})
        screen = Screen(screen_q)
        keyboard = Keyboard(keyboard_q)
        self._peripherals = {periph_map["TERM"]: screen, periph_map["KBD"]: keyboard}

    def __getitem__(self, address):
        if address in self._peripherals:
            return self._peripherals[address].read()
        else:
            return dict.__getitem__(self, address)

    def __setitem__(self, address, data):
        if not isinstance(address, int) or address < 0 or address > 65535:
            raise KeyError(
                f"Memory location {address} must be an int in range [0, 65535]"
            )
        if address in self._peripherals:
            self._peripherals[address].write(data)
        else:
            dict.__setitem__(self, address, data)


class Emulator:
    def __init__(self, filename):
        screen_q = queue.Queue()
        keyboard_q = queue.Queue()
        self._threads = []
        t = threading.Thread(
            name="terminal", target=terminal, args=(screen_q, keyboard_q)
        )
        t.start()
        self._threads.append(t)

        self.memory = Memory(screen_q, keyboard_q)
        self.line_map = {}
        self.variables = {}
        self._load_d8_file(filename, self.memory, self.line_map, self.variables)
        self.reset()
        self.breakpoints = []

    def shutdown(self):
        global stop_threads
        stop_threads = True
        for t in self._threads:
            t.join()  # wait for termination

    def reset(self):
        self.pc = 0
        self.status = {"zero": False, "carry": False, "stop": False}
        self.registers = [0] * 8
        self.ir = 0

    def step(self):
        """Step the CPU by 1 instruction."""
        if not self.status["stop"]:
            self._fetch()
            opcode, operands = self._decode()
            self._execute(opcode, operands)

    def run(self):
        """
        Run the CPU until we hit a breakpoint or Stop flag is true.
        Break out of the loop with CTRL+C in case it hangs
        """
        self.step()  # First step to move away from any breakpoints
        while not self.status["stop"] and self.pc not in self.breakpoints:
            self.step()

    def add_breakpoint(self, address):
        """Add a breakpoint."""
        if address not in self.breakpoints:
            self.breakpoints.append(address)

    def delete_breakpoint(self, address):
        """Delete an existing breakpoint."""
        if address in self.breakpoints:
            self.breakpoints.remove(address)

    def display_source(self, source):
        line_number = self.line_map[self.pc]
        source_line = source[line_number - 1]
        print(f"{line_number} : {source_line}")

    def display_variables(self):
        """Display all the variables and their content."""
        print(f"Status: {self.status}")
        print(f"Registers: {self.registers}\tPC: 0x{self.pc:04x}")
        for name, v in self.variables.items():
            content = [
                self.memory[adr]
                for adr in range(v["address"], v["address"] + v["length"])
            ]
            print(f'{name}[{v["length"]}]: {content}')

    def _load_d8_file(self, filename, memory, line_map, variables):
        """Load the .d8 file in to memory."""
        with open(filename, "r") as f:
            for line in f.readlines():
                mem, line_number, variable = self._parseline(line)
                if mem:
                    memory.update(mem)
                if line_number:
                    line_map.update(line_number)
                if variable:
                    variables.update(variable)

    def load_source(self, filename):
        """
        Load the original source .asm file
        Returns a list of lines that you can index in to
        """
        filename = (
            os.path.splitext(filename)[0] + ".asm"
        )  # TODO should get this from the header in .d8 file
        with open(filename, "r") as f:
            lines = f.readlines()
        lines = [line.rstrip() for line in lines]
        return lines

    def _parseline(self, line):
        """
        Given a line in d8 format, return a dictionary with the key as the address
        and the value as a tuple of (memory contents, line number, variable)
        """
        if line.startswith(";"):
            # Skip comment lines
            return None, None, None
        else:
            line = line.split("|")
            address = int(line[0].strip(), 16)
            value = line[1].strip()
            line_number = int(line[2].strip(), 10)
            debug = line[3].strip()
            if debug.startswith("var:"):
                # Handle variables
                memory = Memory(None, None)  # TODO fix this hack
                result = re.search(r"var\:(\w+)\[(\d+)\]", debug)
                name = result.groups()[0]
                length = int(result.groups()[1], 10)
                for adr, val in zip(range(address, address + length), wrap(value, 2)):
                    memory[adr] = int(val, 16)
                return (
                    memory,
                    {address: line_number},
                    {name: {"length": length, "address": address}},
                )
            else:
                if len(value) == 4:
                    # Handle machine instruction
                    high_byte = int(value[0:2], 16)
                    low_byte = int(value[2:], 16)
                    return (
                        {address: high_byte, address + 1: low_byte},
                        {address: line_number},
                        None,
                    )
                else:
                    raise Exception(f"Error parsing line {line_number}")

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
        opcode = (self.ir & 0b1111100000000000) >> 11
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
        return Rd, Rs1, Rs2

    def _get_reg_opr8u(self, operands):
        """Get 1 register and an 8-bit unsigned value."""
        Rd = operands >> 8
        opr8u = operands & 0xFF
        return Rd, opr8u

    def _get_reg_opr8s(self, operands):
        """Get 1 register and an 8-bit signed value."""
        Rd = operands >> 8
        opr8s = operands & 0xFF
        # Two's complement
        if opr8s > 127:
            offset = opr8s - 2 ** 8
        else:
            offset = opr8s
        return Rd, offset

    def _get_opr11s(self, operands):
        """Get an 11-bit value."""
        opr11s = operands
        # Two's complement
        if opr11s > 1023:
            offset = opr11s - 2 ** 11
        else:
            offset = opr11s
        return offset

    def _execute(self, opc, opr):
        """Execute the current opcode."""
        if opc == "stop":
            self.status["stop"] = True
        elif opc == "ldi":
            Rd, data = self._get_reg_opr8u(opr)
            self.registers[Rd] = data
            # print(f'{map_num_reg[Rd]}<-{data}')
        elif opc == "ldd":
            Rd, lsb = self._get_reg_opr8u(opr)
            address = self.registers[map_reg_num["PAGE"]] << 8 | lsb
            data = self.memory[address]
            self.registers[Rd] = data
            # print(f'{map_num_reg[Rd]}<-{data}<-memory[{address}]')
        elif opc == "ldx":
            Rd, offset = self._get_reg_opr8s(opr)
            address = (
                self.registers[map_reg_num["PAGE"]] << 8
                | self.registers[map_reg_num["X"]] + offset
            )
            data = self.memory[address]
            self.registers[Rd] = data
            # print(f'{map_num_reg[Rd]}<-{data}<-memory[X={address}]')
        elif opc == "ldsp":
            Rd, offset = self._get_reg_opr8s(opr)
            address = (
                self.memory[periph_map["SPPS"]] << 8 | self.registers[map_reg_num["SP"]]
            ) + offset
            data = self.memory[address]
            self.registers[Rd] = data
            # print(f'{map_num_reg[Rd]}<-{data}<-memory[X={address}]')
        elif opc == "std":
            Rs, lsb = self._get_reg_opr8u(opr)
            address = self.registers[map_reg_num["PAGE"]] << 8 | lsb
            data = self.registers[Rs]
            self.memory[address] = data
            # print(f'memory[{address}]<-{data}<-{map_num_reg[Rs]}')
        elif opc == "stx":
            Rs, offset = self._get_reg_opr8s(opr)
            data = self.registers[Rs]
            address = (
                self.registers[map_reg_num["PAGE"]] << 8
                | self.registers[map_reg_num["X"]] + offset
            )
            self.memory[address] = data
            # print(f'memory[{address}]<-{data}<-{map_num_reg[Rs]}')
        elif opc == "stsp":
            Rs, offset = self._get_reg_opr8s(opr)
            data = self.registers[Rs]
            address = (
                self.memory[periph_map["SPPS"]] << 8 | self.registers[map_reg_num["SP"]]
            ) + offset
            self.memory[address] = data
            # print(f'memory[{address}]<-{data}<-{map_num_reg[Rs]}')
        elif opc in ["mov", "nop"]:
            Rd, Rs = self._get_reg_reg(opr)
            data = self.registers[Rs]
            self.registers[Rd] = data
            # print(f'{map_num_reg[Rd]}<-{data}<-{map_num_reg[Rs]}')
        elif opc == "bra":
            self.pc = self.pc + self._get_opr11s(opr)
        elif opc == "beq":
            if self.status["zero"]:
                self.pc = self.pc + self._get_opr11s(opr)
        elif opc == "bne":
            if not self.status["zero"]:
                self.pc = self.pc + self._get_opr11s(opr)
        elif opc == "bcs":
            if self.status["carry"]:
                self.pc = self.pc + self._get_opr11s(opr)
        elif opc == "bcc":
            if not self.status["carry"]:
                self.pc = self.pc + self._get_opr11s(opr)
        elif opc == "bsr":
            data = self.pc & 0xFF  # Low byte first
            address = (
                self.memory[periph_map["SPPS"]] << 8 | self.registers[map_reg_num["SP"]]
            )
            self.memory[address] = data
            self.registers[map_reg_num["SP"]] += -1  # Always post decrement
            data = self.pc >> 8  # High byte
            address = (
                self.memory[periph_map["SPPS"]] << 8 | self.registers[map_reg_num["SP"]]
            )
            self.memory[address] = data
            self.registers[map_reg_num["SP"]] += -1  # Always post decrement
            self.pc = self.pc + self._get_opr11s(opr)  # Then branch
        elif opc == "rts":
            # Because of post increment use the operand to store an offset of 1 so get correct byte from stack
            _, offset = self._get_reg_opr8s(opr)
            address = (
                self.memory[periph_map["SPPS"]] << 8 | self.registers[map_reg_num["SP"]]
            ) + offset
            SPH = self.memory[address]
            self.registers[map_reg_num["SP"]] += 1  # Always post increment
            address = (
                self.memory[periph_map["SPPS"]] << 8 | self.registers[map_reg_num["SP"]]
            ) + offset
            SPL = self.memory[address]
            self.registers[map_reg_num["SP"]] += 1  # Always post increment
            self.pc = SPH << 8 | SPL
        elif opc in [
            "add",
            "adc",
            "inc",
            "sbb",
            "dec",
            "and",
            "or",
            "xor",
            "not",
            "rolc",
            "rorc",
        ]:
            self._alu(opc, opr)
        elif opc in ["clc", "sec"]:
            self.status["carry"] = opc == "sec"
        elif opc == "psh":
            Rs, offset = self._get_reg_opr8s(opr)
            data = self.registers[Rs]
            address = (
                self.memory[periph_map["SPPS"]] << 8 | self.registers[map_reg_num["SP"]]
            ) + offset
            self.memory[address] = data
            self.registers[map_reg_num["SP"]] += -1  # Always post decrement
            # print(f'memory[{address}]<-{data}<-{map_num_reg[Rs]}')
        elif opc == "pul":
            Rd, offset = self._get_reg_opr8s(opr)
            address = (
                self.memory[periph_map["SPPS"]] << 8 | self.registers[map_reg_num["SP"]]
            ) + offset
            data = self.memory[address]
            self.registers[Rd] = data
            self.registers[map_reg_num["SP"]] += 1  # Always post increment
            # print(f'{map_num_reg[Rd]}<-{data}<-memory[X={address}]')
        else:
            # print(self.status)
            # print(self.registers)
            raise Exception(f"Unrecognised opcode: {opc} opr: 0b{opr:011b} ({opr})")

    def _alu(self, opcode, operands):
        """Emulate the ALU execution cycles."""

        def _full_add(Rs1, Rs2, carry):
            """Implement the full adder."""
            Rd = Rs1 + Rs2 + carry
            carry = Rd > 0xFF
            Rd &= 0xFF  # Ensure result in range 0 to 0xFF
            return Rd, carry

        def _sub_with_borrow(Rs1, Rs2, carry):
            """Implement subtract."""
            Rd = Rs1 - Rs2 - carry
            carry = Rd < 0
            Rd = int(
                bin(Rd & 0b11111111), 2
            )  # Convert negative number to 2's complement
            return Rd, carry

        Rd, Rs1, Rs2 = self._get_reg_reg_reg(operands)

        if opcode == "add":
            data, self.status["carry"] = _full_add(
                self.registers[Rs1], self.registers[Rs2], 0
            )
        elif opcode in ["adc", "rolc"]:
            data, self.status["carry"] = _full_add(
                self.registers[Rs1], self.registers[Rs2], self.status["carry"]
            )
        elif opcode == "inc":
            data, self.status["carry"] = _full_add(self.registers[Rs1], 0, 1)
        elif opcode == "sbb":
            # If bit 7 in IR (CMP flag) is set then force carry to 0
            if operands & 0b10000000:
                carry = 0
            else:
                carry = self.status["carry"]
            data, self.status["carry"] = _sub_with_borrow(
                self.registers[Rs1], self.registers[Rs2], carry
            )
        elif opcode == "dec":
            data, self.status["carry"] = _sub_with_borrow(self.registers[Rs1], 0, 1)
        elif opcode == "and":
            data = self.registers[Rs1] & self.registers[Rs2]
            self.status["carry"] = 0
        elif opcode == "or":
            data = self.registers[Rs1] | self.registers[Rs2]
            self.status["carry"] = 0
        elif opcode == "xor":
            data = self.registers[Rs1] ^ self.registers[Rs2]
            self.status["carry"] = 0
        elif opcode == "not":
            data = ~self.registers[Rs1]
            self.status["carry"] = 0
        elif opcode == "rorc":
            # Rotate right through carry
            data = int(self.status["carry"]) << 8
            data |= self.registers[Rs1]
            self.status["carry"] = bool(
                data % 2
            )  # New carry value is the least sig bit
            data = data >> 1

        # Set the status bits
        self.status["zero"] = data == 0

        # If bit 7 in IR (CMP flag) is clear then save the result
        if operands & 0b10000000 == 0:
            self.registers[Rd] = data


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("filename", help=".d8 file to load in to emulator")
    args = parser.parse_args()

    d8 = Emulator(args.filename)
    source = d8.load_source(args.filename)

    while not d8.status["stop"]:
        d8.display_source(source)
        d8.step()
        d8.display_variables()
        input()  # Press Enter to execute next instruction
