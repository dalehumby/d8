# D8 Home-built CPU project
Design and build a custom 8-bit CPU.

I've always wanted to build a computer from the ground up, even as a child/young teen, and this is my attempt to do so. Initially I wanted to build it from relays, but the cost for 1,000+ relays is prohibitively expensive, and based on [other peoples](http://web.cecs.pdx.edu/~harry/Relay/) relay computers it wouldn't be particularly useful. [Ben Eater's tutorials](https://eater.net/8bit) encouraged me to embrace the [7400 series](https://en.wikipedia.org/wiki/List_of_7400-series_integrated_circuits) chipset. I could be a bit more ambitious with my design, and maybe, just _maybe_ have my computer connected to the internet and serve a basic web page.

## Progress
Follow my [build journal](/docs/journal.md)

- [x] Define what I'd like the CPU to do, and what technology I'd like to use
- [x] Design the CPU architecture including data/address busses, registers, addressing modes
- [ ] Implement interrupt handling
- [x] Define the assembly language: [grammar.lark](https://github.com/dalehumby/d8/blob/master/src/grammar.lark)
- [x] [Vim D8 assembler syntax highlighting](https://github.com/dalehumby/vim-d8)
- [x] Write a 2-pass assembler: [asm.py](https://github.com/dalehumby/d8/blob/master/src/asm.py)
- [x] Write an emulator ([emulate.py](https://github.com/dalehumby/d8/blob/master/src/emulate.py)) and GUI front-end ([gui.py](https://github.com/dalehumby/d8/blob/master/src/gui.py)) to step through the and visualise the state of the CPU
- [x] Build the CPU in a digital circuit simulator: [Digital](https://github.com/dalehumby/d8/tree/master/Digital)
- [x] Write small [example programs](https://github.com/dalehumby/d8/tree/master/examples) for testing
- [ ] To test that the CPU and tool chain is any good, implement a basic FORTH or Lisp interpreter
- [ ] Get peripherals working, such as screen, keyboard and timers in emulator and circuit simulator
- [ ] Swap out the high-level digital components for real IC's such as __ series. Source all parts
- [ ] Lay out the PCB and get printed
- [ ] Populate PCB, get the CPU running

## Architecture
For simplicity I have chosen to build an 8-bit [von Neumann](https://en.wikipedia.org/wiki/Von_Neumann_architecture), [RISC](https://en.wikipedia.org/wiki/Reduced_instruction_set_computer) computer. 

The CPU has an 8-bit data bus and 16-bit address bus. All memory and registers are 8-bit and the CPU can operate from any location from 0 to 2^16 (65,535 bytes). 

All instructions are 16-bits in length, and all except the branch and return from subroutine calls take 3 clock cycles to complete (2 instruction fetch cycles + 1 execute cycle.) Pipelining (which I have not implemented) would complete most instructions in 1 cycle.

There are 8 registers: Registers A, B, C, D, E are general purpose. There is a stack pointer (SP) register and an index register (X). The PAGE register sets the high byte of the SP and X registers so the stack and index can reach any memory location in the 65 kB address space.

There is a 16-bit program counter. The CPU supports inherent, immediate, direct, indirect, relative and stack-pointer addressing modes. Words are [big-endian](https://en.wikipedia.org/wiki/Endianness).

The ALU can read from and write to any of the 8 registers, and supports the usual operations such as add (with and without carry), subtract, increment and decrement, left and right shifts through the carry, and the logic operations and, or, xor and not.

Branch operations are based off of the status flags Zero (Z) and Carry/Borrow (C).

Peripherals, such as the keyboard, screen and timers, are memory mapped to addresses in the first 16 bytes of memory.

For further details see the full [CPU Manual](https://docs.google.com/spreadsheets/d/1R_vZknDr0SD-eCZZS5yPU8j0XcCEtsu2B878DS3oAyU/edit?usp=sharing)

