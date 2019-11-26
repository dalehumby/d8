# Journal / notes of what I have done

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
