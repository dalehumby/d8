; Multiply 2 8-bit numbers together, resulting in a 16-bit number

.reset Start

Start:
    LDI     A, 17
    LDI     B, 14
    BSR     Multiply_Sub
    STOP

Multiply_Sub:
    ; C:D = A * B
    LDI     C, 0
    LDI     D, 0
    LDI     X, 0

NextBit:
    CMP     B, X        ; B == 0?
    BEQ     Done        ; If no more bits to multiply by then we're done

    RORC    B, B
    BCC     RotateA

    ADD     D, A, D
    BCC     RotateA     ; If there was a carry in the addition then inc high byte
    INC     C, C		; bug here that needs fixing

RotateA:
    ROLC    A, A        ; Always rotate A
    BEQ     Done
    BRA     NextBit
Done:
    RTS
