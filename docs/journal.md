# Journal / notes of what I have done

## Fri, 11 Dec
Considering adding a `CLR memory` so that can set a value directly in to memory instead of having to load a register first. This would be a store in direct addressing mode but instead of referencing a register those 3 bits would be a value (ie 0..7)

## Tue, 8 Dec 2020: Restarting
After a long lay-off from this project I have restarted it. Work, life and other projects got ahead of me. And I didn't have the energy to refactor the circuit again to build interrupt capability.

I've simplified the mnemonic, and updated the [CPU manual](https://docs.google.com/spreadsheets/d/1R_vZknDr0SD-eCZZS5yPU8j0XcCEtsu2B878DS3oAyU/edit#gid=2004623121)

- Added `CLR` instruction, which is a `LD Rd, 0`
- `INC`, `DEC`, `NOT`, `RORC` and `ROLC` support single register, where source and destination is the same register
- Simplified the load and store mnemonics to just `LD` and `ST`, using an X or SP to specify the addressing mode

## Sat, 28 Dec: Next steps

### Terminal emulator
Now that the basics of screen output is working, I'd like to implement a basic terminal. Digital supports a screen output and keyboard input, which I've mapped to two memory locations. I need to figure out how to get a screen+keyboard working on my emulator. I initially thought of pressing a key combo like CTRL+^ to switch screens like in Vim, or maybe t for terminals, but I feel like I might be on the path to implementing a terminal... so why not have my emulator expose a local telnet port that terminal emulators can connect to? The TCP port can map incoming bytes to the keyboard buffer, and send bytes written to the screen memory location back out on the TCP port to be displayed on the terminal emulator program.

### Interrupts
The other thing I am thinking about is interrupts. That way when a keyboard key comes in and interrupt service routine (ISR) is called, and the keypress can be handled. Similarly for countdown timer reaching 0.

I could add two extra bits to the instruction decoder:
- interrupt pending flag
- interrupt mask

If there is a pending is high and mask is low and CPU clock is 0, the instead of running the load instruction microcode, it would start the interrupt handling microcode
- push program counter high
- push program counter low
- push status
- load ISR high in to PCH
- load ISR low in to PCL

PC pushed to stack is the same as any other branch to subroutine. Issues are:
- I don’t have a "byte" for the status register. I'm not 100% sure I even want a real byte. Maybe I get rid of the E register, and remap registers. Still need to think how I would then get that register on to the stack, and get it off the stack back in to status when ISR returns.
- I'm not sure how the interrupt vector would be defined. I could put the vector in RAM, but how do I get it out of RAM and in to the PC? Because then I need to hardcode (?) the location of the vector in to the microcode. Maybe it's like the reset location, and is actually a BRA instruction that's stored in that location. I could also force the ISR location to be in a specific location in RAM, and there is no vector, or rather the vector is hard coded. But still have to figure out how that vector is encoded in to the microcode.
   - Oh... maybe there can be a bit/command line that reads a hard coded memory location, so when the control line is asserted the location is available on the address bus and can be latched in to the PC. The vector could be stored in two 8-bit registers that are memory mapped, and written/read like the other memory mapped registers.

Come to think of this, I should probably have mapped registers to 0xFFF0? That way there are no wasted bytes in RAM. Not sure how PAGE would be managed.

### Simplification to mnemonics
- `INC X,X` can become `INC X` where the other register is inferred as the same if it is not specified. This can be expanded to `DEC`, `NOT`, `ROLC` and `RORC`
- `LDI X, 0` can become `CLR X`
- Possibly add another addressing mode where can use the low 3 bits of the instruction that's usually used for Rs1 is instead an immediate register used for a signed number, and then can get rid of `INC` and `DEC` instructions and use `ADD X,1` or `ADD X,-1`. This probably needs a new addressing mode, where the 2nd register that is sent to the ALU comes from the addressing module based on bit 3 of the instruction
- Simplify all the load and store to `LD` and `ST` and infer the addressing mode
- Could get rid of the `HALT` instruction completely, and have a special case of all 0's in the instruction meaning halt

## Sat, 28 Dec: Another refactor, to add peripherals
I built some peripherals: screen and keyboard (and the stack pointer page selector.) Real time clock not yet used.

To output a string to the screen, like "Hello World", needed to redefine how variable definitions work. Initially I thought that a variable would be defined like `.data varName 1` for a 1 byte variable named `varName`, and for an array with predefined data something like `.data varName 3 {1,2,3}`. But I haven't found a use for the latter. I _did_ however, find a need to define a string, like `.data str 12 "Hello World"` (Note the 1 extra byte that encodes the null, end-of-string character. I still think that should be explicit, but #TODO need to figure out how C does it, so I try stick to de-facto standards.

As it turned out, my assembler wasn't capable of this, and neither was the .d8 file format. 

I sat down at my laptop earlier in the holiday (in East London) and attempted to do the refactor, but wasn't feeling it. Eventually yesterday afternoon I felt like working again, and spent about 4 hours stripping out the cruft from the assembler (it was outputting symbols and variables that weren't being used by downstream programs), and neatened up the file spec. It now supports variable definitions of arbitrary length, and the variable contents as well as the machine instructions are now hex encoded in the file, instead of binary. I also cleaned up the parsers of the emulator so it didn't rely on a string with 1's and 0's to know it was binary :/ Anyway... a little less hacky/alpha than it was.

The io.asm program in the emulator and the Digital implementation works really nicely! Was super happy with how this came out.

### From my commit notes:
Major refactor of the .d8 file format to handle variables with pre-assigned data
E.g. io.asm: to output a string needs a string defined in memory.
This string is set up as part of the program at assembly time as a variable (or maybe constant?)
but since everything is in RAM then it's really a variable.
.d8 format now supports string definition of .data, and the assembler, emulator and gui understand this new format

Updated the CPU so that the peripherals are assigned addresses [2:6], and RAM as the rest
Tested with my 'hello' program, which does indeed write out 'hello' to the terminal :-D

## Fri, 20 Dec: Completed refactor
Yesterday updated my assembler to understand the new offset addressing (yay no off-by-one errors), and how to code for stack pointer and indirect addressing. This took some time, and there were some subtle bugs but got it right.

The biggest pain is the programmer (me) having to understand the detailed addressing mode and which opcode to use to get what I want. Typing in `LDX    A, 0` which means load a valued found at X+0 in to A, is not so nice. And gets confusing when with `STSP    A, 3`.

I'd rather use one mnemonic for load and store, and let the assembler decide which underlying opcode to use. Maybe 

```
    LD    A, X      ; Load memory at X in to A
    LD    A, X+3    ; Load memory at X+3 in to A
    ST    SP+5, A   ; Store A to the location SP+5
```

- Where the offsets are optional (don’t have to write `+0`, just leave it out.) 
- Destination is always on the left, source on right. 
- Symbol resolves correctly, so could use `SP+LENGTH`.


Anyway, got the assembler working, and then updated the emulator and gui. Once that was done I rewrote the multiply program to use two methods for passing the multiplier and multiplicand: 
- pass pointer (X) and reference using X+0 and X+1 for the high and low byte respectively. The actual value of X is never changed.
- push the two numbers on to the stack then call the multiply subroutine, which references them using SP+3 and SP+4 (the return address is at SP+1 and SP+2.)

Both of these methods worked as well as I had hoped, and simplified the code quite a bit. (Except for all the different types of loads and stores.)

I'm not sure I like either one better, but I am proud of the Stack Pointer version because it uses the stack! And now I have the concept of local variables, which will be nice for the C compiler. (And X for pointers.)

I lay in bed thinking about how I would resolve a function pointer, but don’t know yet. (i.e. storing a branch address in RAM instead of an opcode.) Hacky way would be to push the bytes to stack and then `RTS` but that feels like cheating...


I ran the multiply code on the emulator and Digital circuit and both worked correctly! Made great progress and feeling very excited about the direction of the project.

I was pleasantly surprised with how well using `.origin` and `.data` worked for assigning where in RAM I want the code and data. I even put data in amongst the code, instead of at the top of RAM before the code as I usually do.

Next: Thinking about peripherals, and how I might do interrupts.

I still have available
- 2 opcodes
- 1 addressing mode

If I needed another opcode I could change `STOP` to only stop when the IR is 0x0000 (or even 0xFFFF), and reuse the opcode for anything else that wouldn't trigger stop accidentally. Maybe any of the inherent mode operations are candidates for this reuse.

Because I removed SPCH (shadow program counter high), and moved the SPH (stack pointer high) to RAM, I freed up one of my 8 registers, and added in another general purpose register, E. Not sure I need 5 general purpose registers, especially since I've simplified most of the code by using offset addressing in X and SP, but hey, let's see.

I find myself doing `LDI    A, 0` a fair amount, might implement a `CLR    A` pseudo instruction that is a shortcut. Also there are a number of times where I'm comparing to 0. I see why some CPU's have R0 always set to 0. Perhaps a `CMP    A, 0` instruction wouldn't be too bad, but will think how I might do that. At the moment all my operations are to and from registers. And you can only get values via instructions in to registers. This kind of goes against that philosophy, and would undoubtedly make the CPU more complex.

If I used bit 3 of ALU instructions to tell the CPU that the value in R2 is not a register, but a 3 bit (signed) number, then I could INC (+1), DEC (-1) and CMP (0) easily, and the 3 bit number could code for anything in range -4 to +3. Not a lot, but means I can remove the INC, DEC opcodes, and increment and decrement by numbers other than 1. The ALU probably wouldn’t be any more complex considering the current INC/DEC circuits where ALU1 input is switched out for 0x01 and 0xFF respectively.


## Wed, 18 Dec: Major refactor to add addressing modes

Addressing modes now supported:
- Inherent: No address in the instruction, the opcode itself codes how data is moved around
- Immediate: 8 bit unsigned data stored in the lower byte of the instruction, data moved in to a register
- Direct: 8 bit unsigned integer is the lower byte of the address, combined with the page register to get the address to read/write from
- Indirect: Page:X register gives base address, added to the 8-bit _signed_ integer in the lower byte of the opcode to give an address to read/write from
- Relative: 11 bit signed integer (2's complement) added to the current program counter to give an address to branch to
- Stack pointer: stack pointer page select(high byte), stack pointer (low byte) + 8 bit offset in opcode to give address relative to stack pointer. Also use stack for push/pull bytes, and for storing return address for subroutines.

Phew... this took a number of days to get right, but the process I used was
- decide on the addressing modes I would like, and how they would be encoded in the 16-bit instructions. Draw up a diagram of how busses would like to an 'addressing' decoder and it's 16-bit address. I also added the instructions to my spreadsheet and how they would be encoded, and keeping notes on which instruction used what addressing mode. 
- Once I had a handle on the design I made a circuit design in Digital to test the ideas, and make sure it would work. I also added the stack pointer counter in to this circuit to test how pushing and pulling would work.
- I then took the POC circuit and created a new module in my CPU for addressing, and spent a long time updating the rest of the CPU to work with the stack pointer (instead of the shadow counter)
- I came to the realisation that I didn’t need a 16-bit stack pointer. When I was doing a lot of embedded work the stack didn’t even need to be 255 bytes. So I decided to move the high byte of the stack pointer out of the registers and in to a memory mapped register. (This could be set by dipswitches.) But because I'm trying to design a general purpose CPU (lol) I went for memory mapping the high byte. This can be set at runtime, and then the stack pointer is just the low byte. And that gives 256 bytes of stack space, surely more than enough.
- Because Branch Subroutine (BSR) needs to push the high byte and low byte _and_ branch, I need 3 cycles + 2 for loading the instruction = 5 cycles... which means I now need 3 bits for the cycle counter instead of 2, making the inputs to the CPU controller 10 bits, or 1 kB instead of 512 bytes... annoyingly large.
- (If I want to add an interrupt I probably need another bit, needing 2 kB of instruction codes, yuk!)
- I then updated the CPU controller to input the new 3 bit cycle counter instead of 2 bits; and decided that the controller just outputs the addressing mode ID (3 bits = 8 options), and that saved 1 bit in the output. These modes bits are sent to the address controller which latches the correct values on to the address (or data) bus after doing the sign extension (8- and 11-bit to 16-bit), as offsets to the PC, SP or X registers.
- I also had to add circuits to handle incrementing and decrementing the stack pointer
- And added some nasty circuits to read the high and low byte of the program counter (PC) using the data bus instead of the address bus, so that I could push and pull the bytes during subroutine branches and returns. This is not ideal, but about as simple as I could think. But added another 3 control bits to the control outputs. 
- Control is now we at 10 bits input and 23 bits output.

After all this the circuit worked! With minimal issues and some minor tweaks to the control ROM. (That makerom.py program has been invaluable.)

I tested push and pull; and branch to subroutine and return from subroutine. It was a bit too complex to test much more than that manually coding instructions, so held off until I updated my assembler.

Overall very pleased with how it came out, and how nice this CPU is turning out.

## Tue, 17 Dec: Expanding addressing modes
Now that I have the basic CPU working.... I'm going to take the leap and add in more addressing modes, specifically 
- add the stack pointer, including referencing data offset from the stack pointer; 
- push and pull
- use stack for storing return PC during calls to subroutines
- perhaps (future) use stack for storing CPU state during interrupts
- add relative addressing so all branches are relative to the PC
- add offset to index, so can reference variables ahead or behind the current index (X) register

I've formalised much of my thinking in my spreadsheet that I've been using for recording the microcode
https://docs.google.com/spreadsheets/d/1R_vZknDr0SD-eCZZS5yPU8j0XcCEtsu2B878DS3oAyU/edit#gid=2004623121


## Sun, 15 Dec: Addressing mode fix
Yesterday came across a bug in my initial design, where I was using Direct addressing mode and didn't think deeply enough that there are actually two types of direct addressing: 8-bit and 11-bit.

The 8-bit addressing mode uses lower 8-bits of instruction register as the reference in RAM (low 8 bits of address) for where to load/store data. This is required even if not using the PAGE register for the upper 8-bits of address bus. 

There is also an 11-bit direct addressing mode which is used for branching.

This _could_ be combined, and use page register for branching, but I think this makes the assembler too complex. E.g. if you branch over a page boundary then ... what? Do you change the page? Insert the assembler instruction in to the code to change pages? But then the programmer would never know about the page change and assume that the old page is being use... Terrible idea.

What I _should_ be doing is use offset branching. i.e. those 8 bits (or 11-bits) is a signed number and added to the current program counter (PC) to calculate the new location. I haven't implemented that yet because
- I just want to get the basic CPU working, and don’t want more complex instruction decoding yet
- If I'm going to that trouble, then I would like to add a stack pointer instead of the hacky shadow program counter

Adding all this took a lot of time, but by yesterday night I got the CPU running through the Fibonacci program to the end, correctly. 

This morning I added in a D-type flip-flop to start the run sequence at the right time. There is a subtle interplay between the CPU controller and the program counter, and the various not gates, which causes the CPU to start running out of sequence. I have to only switch to *run* mode while the clock is low (or at least during the falling edge of the clock) which is why I used a D-type flip-flop, and an inverted clock input. Seems to be working reliably now :-)

### Todo:
- [x] add paging to the emulator
- [x] output the RAM hex file from my assembler, so I don't have to do it manually
- [x] finish adding in BCC, BCS
- [x] try some other programs (like multiply)
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
Also been thinking over the last week that I'd like to (if possible...) be able to write a C compiler (or mod an existing compiler) so that I could (maybe???) get a small OS running, like Minix or similar. Wouldn't it be cool if I could boot a small Linux distro? I know it's a far-fetched idea, but I think it'd be more fun if the machine could do something (serve a webpage? respond to a ping over the internet?) than ... basically nothing. This rules out an extensive relay computer build because it's painfully slow, and so limited that it couldn't do much other than some calculations. 

I've been toying with using IC's for logic gates, registers, etc. I know the next step from Relay is probably Valve, or even individual transistors, but I also know my current capability, and interest, is not really in *that* low level design. The fun for me is more the system, like how to join all these components together. 

I'd still like to build a 4-bit relay ALU as a proof of concept. But not go much further than that.

Also, if I build a transistor based CPU I *could* transfer the design to an FPGA in the future. Maybe I do that? And skip all the solering, etc. of discrete components. Maybe not as much fun, but it would be a great excuse to learn Verilog.

Because I want to make a more capable CPU I'm toying with adding a 
- Stack pointer with 8-bit offset addressing mode. i.e. load/store from/to SP +- (8-bit signed offset)
- Stack used for storing return addresses. Include push and pop commands.
- Stack pointer (high and low) are registers like A, B... so can add 'fiddle' with them, specifically to allow C to make space for local variables on the stack.
- Changing branch from 11-bit absolute address to PC +- (11-bit signed offset). This would allow program code to live anywhere in the 65 kB instead of just in the first 2 kB.
- Add a Page register that sets the high byte (upper 8 bits) of the address bus when used with the index (X) register and in direct addressing modes (8 bit). This would allow variables to be anywhere in 65 kB address space, not just in first 256 bytes.

All of this means a much more complex CPU, and specifically building a 16-bit signed adder to calculate addresses. While not too complex, it does mean more addressing modes and therefore more logic to control it all.

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
- Allowing user to make interrupts specifically during 16-bit operations (dealing with high and low bytes) where interrupts cause subtle bugs especially handling of carries.

Possibly keep it simple and just have 1 global interrupt vector, and let that decide which peripheral needs attention and call subroutines from there.

## Sun 1 Dec
Finished up the emulator and GUI, including breakpoints.
Added memory map as a pad in the GUI.

## Mon 25 Nov

Had a look a how to join the GUI experiment with the emulator experiment.
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
- Fibonacci function works :-)

### Todo: Left and right shift
Haven’t implemented yet as 1) don’t know whether I want to shift through carry. Is this a rotate?
Or just a shift? Think I will use in multiply and divide, waiting for GUI implementation before
writing more code. It'll be more fun that way.


## Wrote the assembler
*10 Nov - 13 Nov*

- Forced me to complete the definition of how the commands work, and various addressing modes.
- Came up with basic assembler output that includes some debug (the way the assembler 'thinks' about the file), including line numbers to original source file.
- Fixed many bugs with the assembler
- Made it understand backward references only
- Implemented a 2nd pass so could resolve the backward references
- Resolves references using recursion, so reference can be arbitrarily deep
- Implemented a basic + <literal> for references so can do things like `&address+LENGTH` which is useful for iterating over arrays
  - Just thinking now, might be useful to use this resolver where any literal can be, e.g. `LDI A, 3+5+LENGTH` should also work
