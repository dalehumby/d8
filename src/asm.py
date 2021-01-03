#!/usr/local/bin/python3
"""
Assembler for the D8 CPU

Usage:
    $ python asm.py file.asm

This generates
- file.d8
- file.hex
in the same folder as file.asm

.asm files need to conform to the grammar as defined in grammar.lark

Once assembled, the d8 file can be used by emulate.py to run the emulator, of
in GUI mode using gui.py

The hex file can be loaded in to the CPU simulator's RAM for execution.
"""
import argparse
import os

from lark import Lark, Transformer, UnexpectedCharacters, v_args
from lark.exceptions import VisitError

from d8 import Machine


def load_grammar(filename):
    """Load the Lark EBNF grammar file"""
    with open(filename, "r") as f:
        grammar = f.read()
    return Lark(grammar, start="program", propagate_positions=True)


class SymbolTable:
    """Manage the symbol table."""

    def __init__(self):
        self.symbol_table = {}

    def add(self, key, value):
        """Add a symbol to the table, checking for duplicates."""
        if key in self.symbol_table:
            raise KeyError(f'Symbol "{key}" already defined')
        else:
            self.symbol_table[key.lower()] = value

    def get_all(self):
        """Get full symbol table."""
        return self.symbol_table

    def get(self, key):
        """
        Get a specific key from the table.
        NOTE: Don't catch the KeyError here, catch elsewhere where there is
              more contect eg line numbers
        """
        return self.symbol_table[key.lower()]

    @v_args(inline=True)  # Affects the signatures of the methods
    class EvalExpressions(Transformer):
        """
        Using Lark's Transformer method we can write a transformer for each subtree
        to evaluate our expressions. We also use Python's built in operators for
        doing the maths, and write our own to transform eg hex in to an int.

        Ref https://lark-parser.readthedocs.io/en/latest/visitors.html#transformer
        """

        from operator import add, lshift, mul, neg, rshift, sub
        from operator import truediv as div

        def __init__(self, get_symbol):
            self.get_symbol = get_symbol

        def integer(self, value):
            return int(value)

        def hex(self, value):
            return int(value, 16)

        def char(self, value):
            return ord(value)

        def symbol(self, name):
            return self.get_symbol(name)

    def resolve_expression(self, tree):
        """Take a math expression and resolve it to an int value."""
        try:
            answer = self.EvalExpressions(self.get).transform(tree)
        except VisitError as e:
            print(f"Undefined symbol {e.orig_exc} on line {tree.meta.line}")
            exit(-1)
        try:
            return int(answer.children[0])
        except AttributeError:
            # If answer is not a tree then it's a token
            return int(answer)


class MemoryMap:
    """Map of the entire program space."""

    def __init__(self):
        """Initialise empty memory."""
        self.memory = {}
        self.address = 0

    def set_origin(self, address):
        self.address = address

    def set_reset(self, location):
        """Set the reset location."""
        self.add_instruction(0, "bra", [location], location.meta.line)

    def add_instruction(self, address, op, opr, line_number):
        self.memory[address] = {
            "type": "instruction",
            "op": op.lower(),
            "opr": opr,
            "line_number": line_number,
        }
        self.address += 2

    def add_variable(self, address, symbol, value, line_number):
        self.memory[address] = {
            "type": "variable",
            "symbol": symbol,
            "value": value,
            "line_number": line_number,
        }
        self.address += len(value)

    def get_all(self):
        return self.memory

    def items(self):
        return self.memory.items()

    def get_address(self):
        return self.address


def resolve_directive(node, symbols, memory):
    """Resolve the assembler directives such as .reset .origin .define and .data"""
    if node.data == "reset":
        location = resolve_reset(node.children)
        memory.set_reset(location)
    elif node.data == "origin":
        address = resolve_origin(node, symbols)
        memory.set_origin(address)
    elif node.data == "define":
        resolve_define(node.children, symbols)
    elif node.data == "string":
        resolve_string(node.children, symbols, memory)
    elif node.data == "byte":
        resolve_byte(node.children, symbols, memory)
    elif node.data == "array":
        resolve_array(node.children, symbols, memory)
    else:
        raise NotImplementedError


def resolve_reset(tokens):
    """Resolve the reset to an location, but dont resolve the location to an address yet."""
    tree = tokens[0]
    if tree.data != "symbol":
        raise Exception("Unknown reset type", tree.data)
    return tree


def resolve_origin(node, symbols):
    """Resolve the address of the origin."""
    return symbols.resolve_expression(node)


def resolve_define(tokens, symbols):
    """Add the symbol and value that has been defined to the symbol table."""
    symbol = tokens[0]
    value = symbols.resolve_expression(tokens[1])
    symbols.add(symbol, value)


def resolve_string(tokens, symbols, memory):
    symbol = tokens[0]
    value = tokens[1]
    address = memory.get_address()
    symbols.add(symbol, address)
    value = [ord(x) for x in value[1:-1]]  # Find better way to strip ""
    value.append(0)
    memory.add_variable(address, symbol, value, symbol.line)


def resolve_byte(tokens, symbols, memory):
    """Declare the variable and initialise memory to 0x00."""
    symbol = tokens[0]
    byte_count = symbols.resolve_expression(tokens[1])
    value = [0] * byte_count  # init all bytes to 0
    address = memory.get_address()
    symbols.add(symbol, address)
    memory.add_variable(address, symbol, value, symbol.line)


def resolve_array(tokens, symbols, memory):
    """Declare the variable and define each element in the array to initialise memory."""
    symbol = tokens[0]
    values = [symbols.resolve_expression(element) for element in tokens[1:]]
    address = memory.get_address()
    symbols.add(symbol, address)
    memory.add_variable(address, symbol, values, symbol.line)


def resolve_label(token, symbols, memory):
    """Given a label, resolve it in to an address and save to symbol table."""
    symbols.add(token, memory.get_address())


def resolve_instruction(instruction, memory):
    """Add an instruction to the memory map."""
    memory.add_instruction(
        memory.get_address(),
        instruction.data,
        instruction.children,
        instruction.meta.line,
    )


def build_symbols_memory(source_tree, symbols, memory):
    """Walks the parsed source tree, adding symbols and memory as you go."""
    for line in source_tree.children:
        for item in line.children:
            if item.data == "comment":
                pass
            elif item.data == "directive":
                resolve_directive(item.children[0], symbols, memory)
            elif item.data == "label":
                resolve_label(item.children[0], symbols, memory)
            else:
                resolve_instruction(item, memory)


def build_d8_file(source_filename, symbols, memory):
    """Write the d8 file with the machine instructions and debug info."""
    outlines = []
    machine = Machine(symbols)

    # Write the header of the .d8 file
    out = f"; Assembled {source_filename}\n; Symbols = {symbols.get_all()}\n;Adr | Val  | Ln | Debug info"
    outlines.append(out)
    print(out)

    # Now that we have the complete symbol table, do the second pass
    for address, line in memory.items():
        line_number = line["line_number"]
        if line["type"] == "instruction":
            opcode = line["op"]
            operands = line["opr"]
            m = machine.instruction(address, opcode, operands)
            out = f"{address:04X} | {m:04X} | {line_number:2d} | {opcode} {operands} ({machine.string(m)})"
            outlines.append(out)
            print(out)
        elif line["type"] == "variable":
            hexstr = "".join(f"{v:02X}" for v in line["value"])
            out = f'{address:04X} | {hexstr} | {line_number:2d} | var:{line["symbol"]}[{len(line["value"])}]'
            outlines.append(out)
            print(out)
        else:
            raise Exception(f"Unknown type {line['type']}")

    # Write the .d8 file
    outfile = os.path.splitext(source_filename)[0] + ".d8"
    with open(outfile, "w") as f:
        f.writelines(map(lambda s: s + "\n", outlines))


if __name__ == "__main__":
    argparser = argparse.ArgumentParser(description="Assembler for the D8 CPU")
    argparser.add_argument("source", help="Input file to assemble")
    argparser.add_argument(
        "--check", action="store_true", help="Only check the syntax, don't assemble"
    )
    args = argparser.parse_args()
    source_filename = args.source
    check_syntax = args.check
    with open(source_filename, "r") as f:
        raw_source = f.read()
    asmparser = load_grammar("grammar.lark")
    try:
        source_tree = asmparser.parse(raw_source)
    except UnexpectedCharacters as e:
        print(e)
        exit(-1)

    if check_syntax:
        exit()

    print(source_tree.pretty(), "\n")
    print(source_tree, "\n")

    symbols = SymbolTable()
    memory = MemoryMap()

    # First pass, iterate over file building symbol table and memory map
    build_symbols_memory(source_tree, symbols, memory)

    print("Symbols:\n", symbols.get_all(), "\n")
    print("Memory map:\n", memory.get_all(), "\n")

    # Second pass, resolve all symbols in to values and write machine instructions to output file
    build_d8_file(source_filename, symbols, memory)

    # HEX file output
    # TODO
