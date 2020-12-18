import argparse
import os

from lark import Lark

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
        """Get a specific key from the table."""
        return self.symbol_table[key.lower()]

    def resolve(self, token):
        """
        Resolve the identifier in to an integer.

        Assumes that if the type is SYMBOL then it is already in symbol table
        """
        if isinstance(token, int):
            return token
        elif token.type == "SYMBOL":
            try:
                return self.get(token)
            except KeyError:
                print(
                    f"Undefined symbol {token} at position {token.line}:{token.column}"
                )
                raise
        elif token.type in ["INT", "SIGNED_INT"]:
            return int(token)
        elif token.type == "HEX":
            return int(token, 16)
        elif token.type == "CHAR":
            return ord(token)
        else:
            raise Exception(
                f"Cannot resolve definition for type {token.type} at position {token:line}:{token:column}"
            )

    def to_value(self, tokens):
        """
        Resolve to a value by recursivley resolving each token.

        TODO: Turn this in to a propper calculator with +-*/
              https://github.com/lark-parser/lark/blob/master/examples/calc.py
        """
        address = 0
        sign = 1
        for token in tokens:
            if token.type == "SIGN":
                sign = int(token + "1")  # This is terrible but works
            else:
                address += sign * self.resolve(token)
        return address


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
        self.address += 2

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
        address = resolve_origin(node.children, symbols)
        memory.set_origin(address)
    elif node.data == "define":
        resolve_define(node.children, symbols)
    elif node.data == "string":
        resolve_string(node.children, symbols, memory)
    elif node.data == "byte":
        resolve_byte(node.children, symbols, memory)
    elif node.data == "array":
        # TODO
        raise NotImplementedError


def resolve_reset(tokens):
    """Resolve the reset to an location, but dont resolve the location to an address yet."""
    tree = tokens[0]
    if tree.data != "location":
        raise Exception("Unknown reset type", tree.data)
    return tree


def resolve_origin(tokens, symbols):
    """Resolve the address of the origin."""
    return symbols.to_value(tokens[0].children)


def resolve_define(tokens, symbols):
    """Add the symbol and value that has been defined to the symbol table."""
    symbol = tokens[0]
    value = symbols.resolve(tokens[1])
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
    symbol = tokens[0]
    byte_count = symbols.to_value(tokens[1].children)
    value = [0] * byte_count  # init all bytes to 0
    address = memory.get_address()
    symbols.add(symbol, address)
    memory.add_variable(address, symbol, value, symbol.line)


# TODO array


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
    args = argparser.parse_args()
    source_filename = args.source
    with open(source_filename, "r") as f:
        raw_source = f.read()
    asmparser = load_grammar("grammar.lark")
    source_tree = asmparser.parse(raw_source)

    print(source_tree.pretty(), "\n")
    print(source_tree, "\n")

    symbols = SymbolTable()
    memory = MemoryMap()

    # First pass, iterate over file building symbol table and memory map
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

    print("Symbols:\n", symbols.get_all(), "\n")
    print("Memory map:\n", memory.get_all(), "\n")

    # Second pass, resolve all symbols in to values and write machine instructions to output file
    build_d8_file(source_filename, symbols, memory)

    # HEX file output
    # TODO
