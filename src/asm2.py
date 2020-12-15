import argparse

from lark import Lark


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


def load_grammar(filename):
    """Load the Lark EBNF grammar file"""
    with open(filename, "r") as f:
        grammar = f.read()
    return Lark(grammar, start="program")


def handle_directive(node, symbols):
    """Handle assembler directives such as .reset .origin .define and .data"""
    print(node)
    if node.data == "reset":
        pass
    elif node.data == "origin":
        address = handle_origin(node.children, symbols)
        print(address)
        return address
    elif node.data == "define":
        handle_define(node.children, symbols)
    elif node.data == "data":
        pass


def handle_origin(tokens, symbols):
    tree = tokens[0]
    if tree.data != "location":
        raise Exception("Unknown origin type", tree.data)
    return resolve_location(tree.children, symbols)


def handle_define(tokens, symbols):
    symbol = tokens[0]
    value = resolve_symbol(tokens[1], symbols)
    symbols.add(symbol, value)


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
            return symbols.get(token.value)
        except KeyError:
            raise KeyError(
                f"Undefined symbol {token.value} at position {token.line}:{token.column}"
            )
    elif token.type == "INT":
        return int(token.value)
    elif token.type == "HEX":
        return int(token.value, 16)
    elif token.type == "CHAR":
        return ord(token.value)
    else:
        raise Exception("Cannot resolve definition for type", token.type)


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
    for line in source_tree.children:
        for item in line.children:
            if item.data == "comment":
                pass
            elif item.data == "directive":
                symbl = handle_directive(item.children[0], symbols)
            elif item.data == "label":
                pass
            else:
                # Assume a opcode
                pass
    print(symbols.get_all())
