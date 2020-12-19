; tolower
; Take an ASCII string and make any UPPER CASE letters lower case

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
    LD      SP, &TOPSTACK

Start:
    LD      X, &helloStr
    LD      E, &destStr
Next:
    LD      A, X, 0
    LD      B, #"A"
    CMP     A, B
    BCS     Store       ; If char < "A"
    LD      B, #"Z"
    CMP     B, A
    BCS     Store       ; If char > "Z"
    LD      B, #32
    ADD     A, A, B     ; Change to lower case by adding 32
Store:
    PSH     X           ; Store A in to destStr
    MOV     X, E
    ST      A, X, 0
    PUL     X
    INC     X
    INC     E
    LD      B, #0
    CMP     A, B
    BNE     Next        ; Keep going until find null character
End:
    STOP

.string     helloStr     "Hello WORLD"
.byte       destStr      12
