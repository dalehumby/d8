"""
Run unit tests for the D8 assembler

Usage:
    $ python -m unittest test_asm.py
"""
import unittest

import asm as asm

grammar = asm.load_grammar("grammar.lark")


class TestLoadGrammar(unittest.TestCase):
    def test_load_grammar(self):
        """Test importing the grammar and parsing an empty program."""
        _ = grammar.parse("; This is a comment\n")


class TestSymbolTable(unittest.TestCase):
    def test_add(self):
        symbols = asm.SymbolTable()
        symbols.add("var1", 5)
        with self.assertRaises(KeyError):
            symbols.add("var1", 10)

    def test_get(self):
        symbols = asm.SymbolTable()
        symbols.add("var1", 5)
        self.assertEqual(symbols.get("var1"), 5)
        with self.assertRaises(KeyError):
            symbols.get("notexist")

    def test_get_all(self):
        symbols = asm.SymbolTable()
        symbols.add("var1", 5)
        symbols.add("var2", 10)
        self.assertEqual(symbols.get_all(), {"var1": 5, "var2": 10})

    def test_resolve(self):
        symbols = asm.SymbolTable()
        self.assertEqual(symbols.resolve(1), 1)

        p = grammar.parse(".define LENGTH 10\n")
        token = p.children[0].children[0].children[0].children[1]
        self.assertEqual(symbols.resolve(token), 10)

        p = grammar.parse("LD A, X, -3\n")
        token = p.children[0].children[0].children[1]
        self.assertEqual(symbols.resolve(token), -3)

        p = grammar.parse(".define LENGTH 0x0F\n")
        token = p.children[0].children[0].children[0].children[1]
        self.assertEqual(symbols.resolve(token), 15)

        p = grammar.parse(".define LENGTH 10\n.define WIDTH LENGTH\n")
        symbols.add("length", 10)
        token = p.children[1].children[0].children[0].children[1]
        self.assertEqual(symbols.resolve(token), 10)

        p = grammar.parse('.define LENGTH "A"\n')
        token = p.children[0].children[0].children[0].children[1]
        self.assertEqual(symbols.resolve(token), 65)

    def test_to_value(self):
        symbols = asm.SymbolTable()
        symbols.add("LENGTH", 10)
        p = grammar.parse(".byte myvar LENGTH+1\n")
        tokens = p.children[0].children[0].children[0].children[1].children
        self.assertEqual(symbols.to_value(tokens), 11)


class TestMemoryMap(unittest.TestCase):
    def test_set_origin(self):
        memory = asm.MemoryMap()
        memory.set_origin(100)
        self.assertEqual(memory.get_address(), 100)

    def test_set_reset(self):
        memory = asm.MemoryMap()
        p = grammar.parse(".reset 0x100\n")
        location = p.children[0].children[0].children[0].children[0]
        memory.set_reset(location)
        self.assertEqual(memory.get_address(), 2)
        m = memory.get_all()
        self.assertEqual(m[0]["op"], "bra")
        self.assertEqual(m[0]["type"], "instruction")
        self.assertEqual(m[0]["line_number"], 1)

    def test_add_instruction(self):
        memory = asm.MemoryMap()
        memory.add_instruction(0, "ADD", ["A", "B", "C"], 42)
        m = memory.get_all()
        self.assertEqual(m[0]["type"], "instruction")
        self.assertEqual(m[0]["op"], "add")
        self.assertEqual(m[0]["opr"], ["A", "B", "C"])
        self.assertEqual(m[0]["line_number"], 42)
        self.assertEqual(memory.get_address(), 2)

    def test_add_variable(self):
        memory = asm.MemoryMap()
        memory.add_variable(0, "mystring", [1, 2, 3], 5)
        m = memory.get_all()
        self.assertEqual(m[0]["type"], "variable")
        self.assertEqual(m[0]["symbol"], "mystring")
        self.assertEqual(m[0]["value"], [1, 2, 3])
        self.assertEqual(m[0]["line_number"], 5)
        self.assertEqual(memory.get_address(), 3)


class TestBuildSymbolsMemory(unittest.TestCase):
    """Test the first pass of the assembler."""

    def setUp(self):
        self.symbols = asm.SymbolTable()
        self.memory = asm.MemoryMap()

    def tearDown(self):
        pass
        # print("Symbols:", self.symbols.get_all())
        # print("Memory:", self.memory.get_all())

    def test_reset(self):
        p = grammar.parse(
            """
            .reset Start
            Start:
                STOP
            """
        )
        asm.build_symbols_memory(p, self.symbols, self.memory)
        self.assertEqual(self.symbols.get("start"), 2)
        m = self.memory.get_all()
        self.assertEqual(m[0]["op"], "bra")
        self.assertEqual(m[2]["op"], "stop")

    def test_origin(self):
        p = grammar.parse(
            """
            .origin 0x100
            STOP
            """
        )
        asm.build_symbols_memory(p, self.symbols, self.memory)
        self.assertEqual(self.memory.get_address(), 258)
        m = self.memory.get_all()
        self.assertEqual(m[256]["op"], "stop")

    def test_define(self):
        p = grammar.parse(".define LENGTH 10\n.define WIDTH LENGTH\n")
        asm.build_symbols_memory(p, self.symbols, self.memory)
        self.assertEqual(self.symbols.get("length"), 10)
        self.assertEqual(self.symbols.get("width"), 10)

    def test_label(self):
        p = grammar.parse(
            """
            .reset Start
            .origin 0x100
            Start:
                STOP
            """
        )
        asm.build_symbols_memory(p, self.symbols, self.memory)
        self.assertEqual(self.symbols.get("start"), 256)
        m = self.memory.get_all()
        self.assertEqual(m[0]["op"], "bra")
        self.assertEqual(m[256]["op"], "stop")

    def test_string(self):
        p = grammar.parse(".define LENGTH 10\n.define WIDTH LENGTH\n")
        asm.build_symbols_memory(p, self.symbols, self.memory)
        self.assertEqual(self.symbols.get("length"), 10)
        self.assertEqual(self.symbols.get("width"), 10)

    def test_byte(self):
        p = grammar.parse(
            """
            .byte myvar 2
            .byte i     1
            """
        )
        asm.build_symbols_memory(p, self.symbols, self.memory)
        self.assertEqual(self.symbols.get("myvar"), 0)
        self.assertEqual(self.symbols.get("i"), 2)
        m = self.memory.get_all()
        self.assertEqual(m[0]["value"], [0, 0])
        self.assertEqual(m[2]["value"], [0])

    def test_array(self):
        # TODO
        pass

    def test_instruction(self):
        p = grammar.parse(
            """
            .byte myvar 1
            Start:
                LD A, myvar
            """
        )
        asm.build_symbols_memory(p, self.symbols, self.memory)
        self.assertEqual(self.symbols.get("myvar"), 0)
        m = self.memory.get_all()
        self.assertEqual(m[1]["op"], "ldd")


if __name__ == "__main__":
    unittest.main()
