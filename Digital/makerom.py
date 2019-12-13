"""
Write the ROM control unit of the CPU.
Input: csv file with control instructions
Output: hex file to load in to Digital

https://docs.google.com/spreadsheets/d/1R_vZknDr0SD-eCZZS5yPU8j0XcCEtsu2B878DS3oAyU/edit#gid=0
To calculate the bits

"""

if __name__ == "__main__":
    rom = { address: 0 for address in range(512) }

    # Open csv file, read contents
    with open('micro.csv', 'r') as csv:
        lines = csv.readlines()

    for line in lines[2:]:
        line = line[:-1].split(',')
        opcode = line[1]
        z = line[3]
        c = line[4]
        cycle = line[5]
        output = line[7:-1]
        assert len(output) == 17, len(output)

        output = [ x if x else '0' for x in output ]
        output = int(''.join(output), 2)

        print(f'opc={opcode}, z={z}, c={c}, cy={cycle}, out={output:017b} {output:05X}')

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
            cycle = list(range(4))
        else:
            cycle = [int(cycle)]

        for op in opcode:
            for z_ in z:
                for c_ in c:
                    for cyc in cycle:
                        address = op << 4 | z_ << 3 | c_ << 2 | cyc
                        rom[address] = output
                        print(f'{address:09b} {output:017b}')

    with open('control.hex', 'w') as f:
        f.write('v2.0 raw\n')
        f.writelines(map(lambda s: f'{s:05X}\n', rom.values()))
