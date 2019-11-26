import curses
from emulate import Emulator

def enter_command(screen):
    """Handle command mode."""
    # Create command bar
    height, width = screen.getmaxyx()
    screen.attron(curses.color_pair(1))
    screen.addstr(height-1, 0, ':' + " " * (width - 2))
    screen.move(height - 1, 1)  # Put cursor in status bar
    curses.curs_set(1)  # Switch cursor on
    curses.echo()
    screen.refresh()

    # Capture command
    cmd = screen.getstr(height-1, 1, 20)
    message = handle_command(cmd)

    # Clear command bar
    # todo: print error messages here
    curses.noecho()
    curses.curs_set(0)
    screen.addstr(height-1, 0, " "*(width-1))
    screen.attroff(curses.color_pair(1))

def handle_command(cmd):
    """Handle the command that is typed in.
    cmd is initially a byte array, so turn in to a string"""
    cmd = cmd.decode('utf-8')
    if cmd == 'q':
        quit()


def handle_step(pad, cpu, source):
    """Handle a single step of the CPU."""
    cpu.step()

    # Update row highlighting to next row
    pad.attron(curses.color_pair(2))
    pad.addstr(handle_step.step_row, 1, f'{handle_step.step_row:2d} {handle_step.step_row:04X}  {source[handle_step.step_row]}')
    # Only continue to step if there are more source rows. Note 0 to n-1 for n rows of source
    # todo: rows should be 1-n
    if handle_step.step_row < len(source) - 1:
        handle_step.step_row += 1
        pad.attron(curses.color_pair(1))
        pad.addstr(handle_step.step_row, 1, f'{handle_step.step_row:2d} {handle_step.step_row:04X}  {source[handle_step.step_row]}')

handle_step.step_row = 0

def draw_registers(win, cpu):
    def ir2string(ir):
        """
        Turn the machine code IR in to a printable string.
        Chunk so easy to read
        """
        s = format(ir, '016b')
        return s[0:5] + ' ' + s[5:8] + ' ' + s[8:12] + ' ' + s[12:16]

    def reg2string(reg):
        """Format the registers in to something readable."""
        return f'{format(reg, "3")} 0x{format(reg, "02x")} b{format(reg, "08b")}'

    win.attron(curses.color_pair(2))
    win.addstr(0, 0,   'Registers')
    win.addstr(1, 0,  f'S:{int(cpu.status["stop"])}  C:{int(cpu.status["carry"])}  Z:{int(cpu.status["zero"])}')
    win.addstr(2, 0,  f'A    {reg2string(cpu.registers[0])}')
    win.addstr(3, 0,  f'B    {reg2string(cpu.registers[1])}')
    win.addstr(4, 0,  f'C    {reg2string(cpu.registers[2])}')
    win.addstr(5, 0,  f'D    {reg2string(cpu.registers[3])}')
    win.addstr(6, 0,  f'X    {reg2string(cpu.registers[5])}')
    win.addstr(7, 0,  f'SPCH {reg2string(cpu.registers[6])}')
    win.addstr(8, 0,  f'SPCL {reg2string(cpu.registers[7])}')
    win.addstr(9, 0,  f'PC   0x{format(cpu.pc, "04x")}')
    win.addstr(10, 0, f'INST {ir2string(cpu.ir)}')
    win.noutrefresh()

def draw_variables(win):
    win.attron(curses.color_pair(2))
    win.addstr(0, 0, 'Variables')
    win.addstr(1, 0, 'temp[1]: [0]')
    win.addstr(2, 0, 'fib[10]: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]')
    win.addstr(3, 0, 'return[2]: [0, 0]')
    win.noutrefresh()

def draw_memory(win):
    win.attron(curses.color_pair(2))
    win.addstr(0, 0, 'Memory')
    win.addstr(1, 0, '0000 00 11 22 33 44 55 66 77')
    win.addstr(2, 0, '0008 00 11 22 33 44 55 66 77')
    win.addstr(3, 0, '0010 00 11 22 33 44 55 66 77')
    win.addstr(4, 0, '0018 00 11 22 33 44 55 66 77')
    win.noutrefresh()

def run_emulator(stdscr, filename):
    # Instantiate the emulator, and load the source file
    cpu = Emulator(filename)
    source = cpu.load_source(filename)

    # Clear and refresh the screen for a blank canvas
    stdscr.clear()
    stdscr.refresh()
    height, width = stdscr.getmaxyx()

    # Set up colours
    curses.start_color()
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
    curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_RED, curses.COLOR_BLACK)

    # Source code pad
    source_pad = curses.newpad(len(source), 100)
    source_pad.attron(curses.color_pair(2))
    for y, text in enumerate(source):
        source_pad.addstr(y, 1, f'{y:2d} {y:04X}  {text}')
    top_row = 0

    # Registers window
    reg_win_height = 11
    reg_win_width = 30
    reg_win = curses.newwin(reg_win_height, reg_win_width, 1, width-reg_win_width)

    # Variables window
    var_win_height = 5
    var_win_width = reg_win_width
    var_win = curses.newwin(var_win_height, var_win_width, reg_win_height+2, width-var_win_width)

    # Memory window
    # todo: Memory on a line on its own, with a pad below so can scroll around memory
    mem_win_height = 5
    mem_win_width = reg_win_width
    mem_win = curses.newwin(mem_win_height, mem_win_width, reg_win_height+var_win_height+2, width-mem_win_width)

     # Render title bar
    stdscr.attron(curses.color_pair(1))
    stdscr.addstr(0, 0, filename)
    stdscr.addstr(0, len(filename), " " * (width - len(filename) - 1))
    stdscr.attroff(curses.color_pair(1))

    # Render the command bar
    curses.curs_set(0)
    stdscr.attron(curses.color_pair(1))
    stdscr.addstr(height-1, 0, " "*(width-1))
    stdscr.attroff(curses.color_pair(1))

    k = 0
    while True:
        # Code window
        if k == ord(':'):
            enter_command(stdscr)
        elif k == curses.KEY_DOWN:
            top_row += 1
            top_row = min(len(source)-height+2, top_row)
        elif k == curses.KEY_UP:
            top_row -= 1
            top_row = max(0, top_row)
        elif k == ord('s'):
            handle_step(source_pad, cpu, source)

        # Breakpoints
        # todo: update breakpoints from the command mode
        source_pad.attron(curses.color_pair(3))
        source_pad.addch(21, 0, '●', curses.A_BOLD)

        # Update the screen
        source_pad.noutrefresh(top_row, 0, 1, 0, height-2, width-reg_win_width)

        # Update screen
        draw_registers(reg_win, cpu)
        draw_variables(var_win)
        draw_memory(mem_win)

        # Refresh the screen
        curses.doupdate()

        # Wait for next input
        k = stdscr.getch()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('filename', help='.d8 file to load in to emulator')
    args = parser.parse_args()

    curses.wrapper(run_emulator, args.filename)
