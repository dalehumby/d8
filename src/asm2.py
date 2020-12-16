import argparse

from lark import Lark


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
            raise Exception(f'Symbol "{key}" already defined')
        else:
            self.symbol_table[key.lower()] = value

    def get_all(self):
        """Get full symbol table."""
        return self.symbol_table

    def get(self, key):
        """Get a specific key from the table."""
        return self.symbol_table[key.lower()]


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
        self.add_instruction(0, "bra", location, None)
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

    def get_address(self):
        return self.address


def resolve_directive(node, symbols, memory):
    """Resolve the assembler directives such as .reset .origin .define and .data"""
    print(node)
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
        pass
    elif node.data == "array":
        pass


def resolve_reset(tokens):
    """Resolve the reset to an location, but dont resolve the location to an address yet."""
    tree = tokens[0]
    if tree.data != "location":
        raise Exception("Unknown reset type", tree.data)
    return tree.children


def resolve_origin(tokens, symbols):
    """Resolve the address of the origin."""
    tree = tokens[0]
    if tree.data != "location":
        raise Exception("Unknown origin type", tree.data)
    return resolve_location(tree.children, symbols)


def resolve_define(tokens, symbols):
    """Add the symbol and value that has been defined to the symbol table."""
    symbol = tokens[0]
    value = resolve_symbol(tokens[1], symbols)
    symbols.add(symbol, value)


def resolve_string(tokens, symbols, memory):
    symbol = tokens[0]
    value = tokens[1]
    address = memory.get_address()
    symbols.add(symbol, address)
    value = [ord(x) for x in value[1:-1]]  # Find better way to strip ""
    value += "\0"
    memory.add_variable(address, symbol, value, symbol.line)


# TODO byte
# TODO array


def resolve_location(tokens, symbols):
    """
    Resolve the location by recursivley resolving each token.

    TODO: Turn this in to a propper calculator with +-*/
          https://github.com/lark-parser/lark/blob/master/examples/calc.py
    """
    address = 0
    sign = 1
    for token in tokens:
        if token.type == "SIGN":
            sign = int(token + "1")
        else:
            address += sign * resolve_symbol(token, symbols)
    return address


def resolve_symbol(token, symbols):
    """
    Resolve the identifier in to an integer.

    Assumes that if the type is NAME then it is already in symbol table
    """
    if token.type == "SYMBOL":
        try:
            return symbols.get(token)
        except KeyError:
            raise KeyError(
                f"Undefined symbol {token} at position {token.line}:{token.column}"
            )
    elif token.type == "INT":
        return int(token)
    elif token.type == "HEX":
        return int(token, 16)
    elif token.type == "CHAR":
        return ord(token)
    else:
        raise Exception("Cannot resolve definition for type", token.type)


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


if __name__ == "__main__":
    argparser = argparse.ArgumentParser(description="Assembler for the D8 CPU")
    argparser.add_argument("source", help="Input file to assemble")
    args = argparser.parse_args()
    source_file = args.source
    with open(source_file, "r") as f:
        raw_source = f.read()
    asmparser = load_grammar("grammar.lark")
    source_tree = asmparser.parse(raw_source)

    print(source_tree.pretty())
    print(source_tree)

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

    print(symbols.get_all())
    print(memory.get_all())

    # Second pass, resolve all symbols in to values and write machine instructions to output file
    # TODO
