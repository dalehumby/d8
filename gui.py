import curses

def draw_menu(stdscr):
    k = 0

    # Clear and refresh the screen for a blank canvas
    stdscr.clear()
    stdscr.refresh()
    height, width = stdscr.getmaxyx()

    # Start colors in curses
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
    step_row = 0

    # Registers window
    registers_win_height = 11
    registers_win_width = 30
    registers_win = curses.newwin(registers_win_height, registers_win_width, 1, width-registers_win_width)

    # Variables window
    var_win_height = 5
    var_win_width = registers_win_width
    var_win = curses.newwin(var_win_height, var_win_width, registers_win_height+2, width-var_win_width)

    # Memory window
    # todo: Memory on a line on its own, with a pad below so can scroll around memory
    mem_win_height = 5
    mem_win_width = registers_win_width
    mem_win = curses.newwin(mem_win_height, mem_win_width, registers_win_height+var_win_height+2, width-mem_win_width)


    # Loop where k is the last character pressed
    while (k != ord('q')):

        # Initialization
        #stdscr.clear()
        height, width = stdscr.getmaxyx()

         # Render title bar
        stdscr.attron(curses.color_pair(1))
        stdscr.addstr(0, 0, filename)
        stdscr.addstr(0, len(filename), " " * (width - len(filename) - 1))
        stdscr.attroff(curses.color_pair(1))

        # Render status bar
        statusbarstr = ':'
        stdscr.attron(curses.color_pair(1))
        stdscr.addstr(height-1, 0, statusbarstr)
        stdscr.addstr(height-1, len(statusbarstr), " " * (width - len(statusbarstr) - 1))
        stdscr.attroff(curses.color_pair(1))

        # Put cursor in status bar
        stdscr.move(height - 1, len(statusbarstr) + 1)


        # Code window
        if k == curses.KEY_DOWN:
            top_row += 1
            top_row = min(len(source)-height+2, top_row)
        elif k == curses.KEY_UP:
            top_row -= 1
            top_row = max(0, top_row)
        elif k == ord('s'):
            source_pad.attron(curses.color_pair(2))
            source_pad.addstr(step_row, 1, f'{step_row:2d} {step_row:04X}  {source[step_row]}')
            step_row += 1
            source_pad.attron(curses.color_pair(1))
            source_pad.addstr(step_row, 1, f'{step_row:2d} {step_row:04X}  {source[step_row]}')

        # Breakpoints
        source_pad.attron(curses.color_pair(3))
        source_pad.addch(21, 0, '●', curses.A_BOLD)

        source_pad.noutrefresh(top_row, 0, 1, 0, height-1, width-registers_win_width)


        # Registers window
        registers_win.attron(curses.color_pair(2))
        registers_win.addstr(0, 0, 'Registers')
        registers_win.addstr(1, 0, 'S:0  C:0  Z:1')
        registers_win.addstr(2, 0, 'A    255 0xFF b10101100')
        registers_win.addstr(3, 0, 'B    b10101100 0xFF 255')
        registers_win.addstr(4, 0, 'C    b10101100 0xFF 255')
        registers_win.addstr(5, 0, 'D    b10101100 0xFF 255')
        registers_win.addstr(6, 0, 'X    b10101100 0xFF 255')
        registers_win.addstr(7, 0, 'SPCH b10101100 0xFF 255')
        registers_win.addstr(8, 0, 'SPCL b10101100 0xFF 255')
        registers_win.addstr(9, 0, 'PC   0xFFFF')
        registers_win.addstr(10, 0, 'INST 11100 111 0111 0111')
        registers_win.noutrefresh()


        # Variables windown
        var_win.attron(curses.color_pair(2))
        var_win.addstr(0, 0, 'Variables')
        var_win.addstr(1, 0, 'temp[1]: [0]')
        var_win.addstr(2, 0, 'fib[10]: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]')
        var_win.addstr(3, 0, 'return[2]: [0, 0]')
        var_win.noutrefresh()

        # Memory window
        mem_win.attron(curses.color_pair(2))
        mem_win.addstr(0, 0, 'Memory')
        mem_win.addstr(1, 0, '0000 00 11 22 33 44 55 66 77')
        mem_win.addstr(2, 0, '0008 00 11 22 33 44 55 66 77')
        mem_win.addstr(3, 0, '0010 00 11 22 33 44 55 66 77')
        mem_win.addstr(4, 0, '0018 00 11 22 33 44 55 66 77')
        mem_win.noutrefresh()

        # Refresh the screen
        curses.doupdate()

        # Wait for next input
        k = stdscr.getch()


if __name__ == "__main__":
    # load file

    filename = 'fib.asm'
    with open(filename, 'r') as f:
        source = f.readlines()
    source = [ line.rstrip() for line in source ]

    curses.wrapper(draw_menu)
