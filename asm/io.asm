; Program to test input and output

; Memory mapped register definitions in PAGE 0
.define    SPPS    0x02      ; Stack pointer page select
.define    TERM    0x03      ; Terminal output
.define    KBD     0x04      ; Keyboard input
.define    RTCH    0x05      ; RTC high byte
.define    RTCL    0x06      ; RTC low byte

.define    TOPSTACK 0x0F
.reset     Init

.origin    TOPSTACK+1
Init:
    LDI    PAGE, 0
    STD    PAGE, SPPS
    LDI    SP, TOPSTACK

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
