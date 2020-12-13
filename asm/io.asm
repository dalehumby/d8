; Program to test input and output

; Memory mapped register definitions in PAGE 0
.define     SPPS    0x02    ; Stack pointer page select
.define     TERM    0x03    ; Terminal output
.define     KBD     0x04    ; Keyboard input
.define     RTCH    0x05    ; RTC high byte
.define     RTCL    0x06    ; RTC low byte

.define     TOPSTACK 0x0F
.reset      Init

.origin     TOPSTACK+1
Init:
    CLR     PAGE
    ST      PAGE, SPPS
    LD      SP, #TOPSTACK

Start:
    LD      X, &helloStr
    CLR     E
Next:
    LD      A, X, 0
    CMP     A, E
    BEQ     End
    ST      A, TERM
    INC     X
    BRA     Next
End:
    STOP

.data       helloStr     10 "hello"
