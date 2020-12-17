; Test the assembler, grammar and parsers by assembling each instruciton
; *** This program is not supposed to execute ***

.define     LENGTH      10
.define     WIDTH       LENGTH
.define     TOPSTACK    0xFF

.reset      Start
.byte       key         1

.origin     TOPSTACK+1
Start:
    ; Loads
    LD      A, key
    LD      A, &key
    LD      B, #3
    LD      SP, &TOPSTACK
    LD      PAGE, X, -1
    LD      E, SP, 7

    ; Stores
    ST      A, key
    ST      B, X, -1
    ST      C, SP, 2

    ; Register
    CLR     A
    MOV     B, C

    ; Status flags
    CLC
    SEC
    STOP

    ; Branches
    CMP     A, B
    BRA     Start
    BCC     Start
    BCS     Start
    BEQ     Start
    BNE     Start
    BSR     Start
    RTS

    ; Arithmetic
    ADD     A, B, C
    ADC     D, E, SP
    INC     A, B
    INC     C
    SBB     A, B, C
    DEC     D, E
    DEC     PAGE
    ROLC    A, B
    ROLC    A
    RORC    C, D
    RORC    E
    AND     A, B, C
    OR      A, B, C
    XOR     A, B, C
    NOT     A, B
    NOT     A

    ; Stack
    PSH     A
    PUL     B

    NOP

.string     helloStr    "Hello WORLD"
.byte       fib         LENGTH
;;;;.array  vector   { 1, 2, "C", 0x0F }
