; Test the assembler, grammar and parsers by assembling each instruciton
; >>> This program is supposed to assemble but is not designed to execute <<<
;*******************************************************************************************
; STYLE GUIDE
; DEFINES, MACROS and ASSEMBLER OPCODES (LD)
; , space; space around +-*/
; Jump points are PascalCase: MainLoop
; Tabs are four spaces, and tabs are converted to spaces. Trailing whitespace should be removed
; Subroutines are PascalCase with _Sub postfix: StreamBytes_Sub
; Variables are camelCase: dataBufferAddress
; Opcode in col 5, operands in col 13 and 25, comments col 41 (or at least aligned in that block of code.)
;*******************************************************************************************

.define     LENGTH      10              ; This is an inline comment
.define     WIDTH       LENGTH
.define     TOPSTACK    0xFF
.define     EXPRESSION  1 + 2 * (-3 + 4) / "A"

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
