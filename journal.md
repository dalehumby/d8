# Journal / notes of what I have done

## Sun, 15 Dec: Addressing mode fix
Yesterday came across a bug in my initial design, where I was using Direct addressing mode and didn't think deeply enough that there are actually two types of direct addressing: 8-bit and 11-bit.

The 8-bit addressing mode uses lower 8-bits of instruction register as the reference in RAM (low 8 bits of address) for where to load/store data. This is required even if not using the PAGE register for the upper 8-bits of address bus. 

There is also an 11-bit direct addressing mode which is used for branching.

This _could_ be combined, and use page register for branching, but I think this makes the assembler too comples. E.g. if you branch over a page boundary then ... what? Do you change the page? Insert the assembler instruction in to the code to change pages? But then the programmer would never know about the page change and assume that the old page is being use... Terrible idea.

What I _should_ be doing is use offset branching. i.e. those 8 bits (or 11-bits) is a signed number and added to the current program counter (PC) to calculate the new location. I haven't implemented that yet because
- I just want to get the basic CPU working, and dont want more complex instruction decoding yet
- If I'm going to that trouble, then I would like to add a stack pointer instead of the hacky shaddow program counter

Adding all this took a lot of time, but by yesterday night I got the CPU running through the Fibonacci program to the end, correctly. 

This morning I added in a D-type flip-flop to start the run sequence at the right time. There is a subtle interplay between the CPU controller and the program counter, and the various not gates, which causes the CPU to start running out of sequence. I have to only switch to *run* mode while the clock is low (or at least during the falling edge of the clock) which is why I used a D-type flip-flop, and an inverted clock input. Seems to be working reliably now :-)

### Todo:
- [ ] add paging to the emulator
- [x] output the RAM hex file from my assembler, so I don't have to do it manually
- [ ] finish adding in BCC, BCS
- [ ] try some other programs (like multiply)
- [ ] try link Digital to my emulator using its TCP/IP protocol
- [ ] add a peripheral? screen or keyboard?


## Sat, 14 Dec: Design changes
Despite the circuit having a paging register, I think I am getting ahead of myself. So:
1. Going to keep an 11-bit direct addressing mode, and therefore not use the page register for branches. This means that all code (for now) must be in the first 2048 bytes of memory.
2. I _will_ use the page register for indirect addressing mode, so in effect

## Wed 11 Dec: Design of circuits
The last few days been working on the CPU simulator using 'Digital', and digital circuit simulator written by a prof. to teach design to his students. Pretty cool, and not too buggy. Also seems that it presents a TCP port that you can connect an emulator/IDE to and step through your circuit and code at the same time.

I've created
- registers
- program counter
- ALU
- instruction register and wires to pull out the various opcodes and operands.

Todo:
- controller and state machine
- clock with halt bit
- status code register

## Sun 8 Dec: Major rethink
Watched many of [Ben Eater's](https://eater.net/8bit) 8-bit CPU build videos yesterday. Basically all of them.
Also been thinking over the last week that I'd like to (if possible...) be able to write a C compiler (or mod an existing compiler) so that I could (maybe???) get a small OS running, like Minix or similar. Wouldn't it be cool if I could boot a small Linux distro? I know it's a far-fetched idea, but I think it'd be more fun if the machine could do something (servre a webpage? respond to a ping over the internet?) than ... basically nothing. This rules out an extensive relay computer build because it's painfully slow, and so limited that it couldn't do much other than some calculations. 

I've been toying with using IC's for logic gates, registers, etc. I know the next step from Relay is probably Valve, or even individual transistors, but I also know my current capability, and interest, is not really in *that* low level design. The fun for me is more the system, like how to join all these components together. 

I'd still like to build a 4-bit relay ALU as a proof of concept. But not go much further than that.

Also, if I build a transistor based CPU I *could* transfer the design to an FPGA in the future. Maybe I do that? And skip all the solering, etc. of discrete components. Maybe not as much fun, but it would be a great excuse to learn Verilog.

Because I want to make a more capable CPU I'm toying with adding a 
- Stack pointer with 8-bit offset addressing mode. i.e. load/store from/to SP +- (8-bit signed offset)
- Stack used for storing return addresses. Include push and pop commands.
- Stack pointer (high and low) are registers like A, B... so can add 'fiddle' with them, specifically to allow C to make space for local variables on the stack.
- Changing branch from 11-bit absolute address to PC +- (11-bit signed offset). This would allow program code to live anywhere in the 65 kB instead of just in the first 2 kB.
- Add a Page register that sets the high byte (upper 8 bits) of the address bus when used with the index (X) register and in direct addressing modes (8 bit). This would allow variables to be anywhere in 65 kB address space, not just in first 256 bytes.

All of this means a much more complex CPU, and specifically bulding a 16-bit signed adder to calculate addresses. While not too complex, it does mean more addressing modes and therefore more logic to control it all.

I drew up the diagrams for controlling the registers, and gating them on to the data bus or ALU source 0 (S0) and source 1 (S1) busses, and .... yeah, there's a ton of work for each register. This is because any register can be connected to the ALU, instead of e.g. always connecting register A and B to the ALU and outputting to register C. Even if it's complex I'd still want to do this - Writing code and emulating has proven its worth here.

### Language
- C... obviously
- What about a Lisp? Maybe that could be implemented? Not too familiar but seems like it might be a thing
- Lua? Apparently it's designed to have a small footprint. Not sure if small enough, or add any value over C
- Basic? hahaha

### Peripherals
I'd like to add memory mapped IO, like a screen, keyboard buffer, timers, Tx/Rx for serial IO (to an old school terminal, with form feed printout and a keyboard build in?), and even some digital IO pins for fun stuff like turning on lights and buzzer, or getting input from a device.

I don't yet understand how a peripheral and the CPU share access to RAM, but I guess a peripheral only accesses the RAM when the CPU is not, so during a quiet cycle, or the CPU has an extra cycle at the end of each instruction where peripherals can update stuff.

### Interrupts
... I've not given implementation too much thought, but it would be interesting if I could figure out how this would be done. Challenges are
- detect interrupt
- push current state of CPU to stack
- load correct interrupt service routine in to PC 
- masking interrupts while handling current interrupt
- Allowing user to mase interrupts specifically during 16-bit operations (dealing with high and low bytes) where interrupts cause subtle bugs especially handling of carries.

Possibly keep it simple and just have 1 global interrupt vector, and let that decide which peripheral needs attention and call subroutines from there.

## Sun 1 Dec
Finished up the emulator and GUI, including breakpoints.
Added memory map as a pad in the GUI.

## Mon 25 Nov

Had a look a how to join the GUI experiemnt with the emulator experiment.
My current thinking is that I should refactor the emulator in to OOP, so 
the emulator itself is a class, with state (of the cp), and methods to
control its state.

The GUI will be the main container of the application, and control the stepping
of the CPU based on commands (s for step, r for run), setting breakpoints, etc.

Todo
  - refactor

## Playing with GUI ideas
*18 Nov*


## Wrote an emulator
*17-18 Nov*
- Loads the d8 file, and the code from the asm file
- Steps through the code when press Enter
- Most functionality that I need is there
- Fibbonacci function works :-)

### Todo: Left and right shift
Havne't implemented yet as 1) dont know whether I want to shift through carry. Is this a rotate?
Or just a shift? Think I will use in multiply and divide, waiting for GUI implementation before
writing more code. It'll be more fun that way.


## Wrote the assembler
*10 Nov - 13 Nov*

- Forced me to complete the definition of how the commands work, and various addressing modes.
- Came up with basic assembler output that includes some debug (the way the assembler 'thinks' about the file), including line numbers to original source file.
- Fixed many bugs with the assembler
- Made it understand backward references only
- Implemented a 2nd pass so could resolve the backward references
- Resolves references using recursion, so reference can be arbitarily deep
- Implemented a basic + <literal> for references so can do things like `&address+LENGTH` which is useful for iterating over arrays
  - Just thinking now, might be useful to use this resolver where any literal can be, e.g. `LDI A, 3+5+LENGTH` should also work
