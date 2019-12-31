; Multiply 2 8-bit numbers together, resulting in a 16-bit product

; Memory mapped register definitions in PAGE 0
.define    SPPS    0x02      ; Stack pointer page select

.reset Init

.origin 0x10
Init:
    LDI     PAGE, 0
    STD     PAGE, SPPS
    LDI     SP, 0x0F

Start:
    ; Multiply, putting the two numbers on to the stack
    LDI    A, 5
    PSH    A
    LDI    A, 10
    PSH    A
    BSR    MultiplySP_Sub
    PUL    A                ; Get high byte of product
    PUL    B                ; Get low byte of product

    ; Multiply passing in the two numbers using a pointer (the X register)
    LDI     A, 2
    STD     A, multiply
    LDI     A, 0xFF
    STD     A, multiply+1
    LDI     X, &multiply     ; load X with the pointer in memory for what want to multiply
    BSR     MultiplyPtr_Sub

    STOP


MultiplySP_Sub:
    ; [SP+3:SP+4] = [SP+3] * [SP+4]
    ; Use A:B as the shift left register and C as the shift right register; store partial product in SP+3:SP+4
    LDI     A, 0       ; High byte of shift register (A:B) is 0
    LDSP    B, 3       ; Low byte of shift register is multiplier, which is at location SP+3
    LDSP    C, 4       ; C is the multiplicand, at location SP+4
    STSP    A, 3       ; Clear high byte in RAM
    STSP    A, 4       ; Clear low byte in RAM

    LDI     E, 0
NextBitSP:
    CMP     C, E        ; C == 0?
    BEQ     DoneSP      ; If no more bits to multiply by then we're done

    RORC    C, C        ; Do we need to do an add?
    BCC     RotateABSP  ; If not then skip

    LDSP    D, 4        ; Else we need to do the add, low byte first
    ADD     D, B, D
    STSP    D, 4
    LDSP    D, 3        ; load the intermediate product (high byte)
    ADC     D, A, D     ; Add the high byte intermidiate product with the shifted high byte of multiplicand, plus any carry bit from previous add
    STSP    D, 3        ; Store high byte

RotateABSP:
    ROLC    B, B        ; Always rotate A:B
    ROLC    A, A        ; Shift the MSB of B in to A
    BRA     NextBitSP
DoneSP:
    RTS

.data  multiply 2      ; Declare variable for multiplication
MultiplyPtr_Sub:
    ; [X:X+1] = [X] * [X+1]
	; Use A:B as the shift left register and C as the shift right register; store partial sum in X:X+1
    LDI     A, 0       ; High byte of shift register (A:B) is 0
    LDX     B, 0       ; Low byte of shift register is first number
    LDX     C, 1       ; C is the other number to multiply by
    STX     A, 0       ; Clear high byte in RAM
    STX     A, 1       ; Clear low byte in RAM

    LDI     E, 0
NextBit:
    CMP     C, E        ; C == 0?
    BEQ     Done        ; If no more bits to multiply by then we're done

    RORC    C, C        ; Do we need to do an add?
    BCC     RotateAB    ; If not then skip

    LDX     D, 1        ; Else we need to do the add, low byte first
    ADD     D, B, D
    STX     D, 1
    LDX     D, 0        ; load the intermediate sum (high byte)
    ADC     D, A, D     ; Add the high byte intermidiate sum with the shifted high byte of multiplicand, plus any carry bit from previous add
    STX     D, 0        ; Store high byte

RotateAB:
    ROLC    B, B        ; Always rotate A:B
    ROLC    A, A        ; Shift the MSB of B in to A
    BRA     NextBit
Done:
    RTS
