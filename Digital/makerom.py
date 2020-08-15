"""
Write the ROM microcode control unit of the CPU.
Input: micro.csv with control instructions
Output: hex file to load in to Digital circuit cimulator

Save the Microcode tab as micro.csv
https://docs.google.com/spreadsheets/d/1R_vZknDr0SD-eCZZS5yPU8j0XcCEtsu2B878DS3oAyU/edit#gid=0

"""

if __name__ == "__main__":
    rom = { address: 0 for address in range(1024) }

    # Open microcode csv file, read contents
    with open('micro.csv', 'r') as csv:
        lines = csv.readlines()

    for line in lines[4:]:
        line = line.split(',')
        print(line)
        opcode = line[1]
        z = line[3]
        c = line[4]
        cycle = line[5]
        output = line[7:-4]
        assert len(output) == 23, len(output)

        output = [ x if x else '0' for x in output ]
        output = int(''.join(output), 2)

        print(f'opc={opcode}, z={z}, c={c}, cy={cycle}, out={output:023b} {output:06X}')

        if opcode == 'X':
            opcode = list(range(32))
        else:
            opcode = [int(opcode)]

        if z == 'X':
            z = list(range(2))
        else:
            z = [int(z)]

        if c == 'X':
            c = list(range(2))
        else:
            c = [int(c)]

        if cycle == 'X':
            cycle = list(range(8))
        else:
            cycle = [int(cycle)]

        for op in opcode:
            for z_ in z:
                for c_ in c:
                    for cyc in cycle:
                        address = op << 5 | z_ << 4 | c_ << 3 | cyc
                        rom[address] = output
                        print(f'{address:010b} {output:023b}')

    with open('control.hex', 'w') as f:
        f.write('v2.0 raw\n')
        f.writelines(map(lambda s: f'{s:06X}\n', rom.values()))
