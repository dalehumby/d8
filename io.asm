; Program to test input and output

; Memory mapped register definitions in PAGE 0
.define    SPPS    0x02      ; Stack pointer page select
.define    TERM    0x03      ; Terminal output
.define    KBD     0x04      ; Keyboar input

.reset Init

.origin 0x10
Init:
    LDI    PAGE, 0
    LDI    A, 0x00
    STD    A, SPPS
    LDI    SP, 0x0F

Start:
    LDI    X, &helloStr
    LDI    E, 0
Next:
    LDX    A, 0
    CMP    A, E
    BEQ    End
    STD    A, TERM
    INC    X, X
    BRA    Next
End:
    STOP

.data      helloStr     10 "hello"
