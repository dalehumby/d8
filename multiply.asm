; Multiply 2 8-bit numbers together, resulting in a 16-bit number

.reset Start

Start:
    LDI     A, 16
    LDI     B, 16
    BSR     Multiply_Sub
    STOP

Multiply_Sub:
    ; C:D = A * B (Use X as working memory)
    LDI     C, 0
    LDI     D, 0

NextBit:
    CMP     B, C        ; B == 0?
    BEQ     Done        ; If no more bits to multiply by then we're done

    RORC    X, B
    MOV     B, X
    BCC     RotateA

    ADD     X, A, D
    MOV     D, X
    BCC     RotateA     ; If there was a carry in the addition then inc high byte
    INC     X, C
    MOV     C, X

RotateA:
    ROLC    X, A        ; Always rotate A
    BEQ     Done
    MOV     A, X
    BRA     NextBit
Done:
    RTS
