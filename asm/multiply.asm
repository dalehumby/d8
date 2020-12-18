; Multiply 2 8-bit numbers together, resulting in a 16-bit product

; Memory mapped register definitions in PAGE 0
.define    SPPS    0x02      ; Stack pointer page select

.reset Init

.origin 0x10
Init:
    CLR     PAGE
    ST      PAGE, SPPS
    LD      SP, #0x0F

Start:
    ; Multiply, putting the two numbers on to the stack
    LD     A, #5
    PSH    A
    LD     A, #10
    PSH    A
    BSR    MultiplySP_Sub
    PUL    A                ; Get high byte of product
    PUL    B                ; Get low byte of product

    ; Multiply passing in the two numbers using a pointer (the X register)
    LD      A, #2
    ST      A, multiply
    LD      A, #0xFF
    ST      A, multiply+1
    LD      X, &multiply     ; load X with the pointer in memory for what want to multiply  <-- check this: Was LDI
    BSR     MultiplyPtr_Sub

    STOP


MultiplySP_Sub:
    ; [SP+3:SP+4] = [SP+3] * [SP+4]
    ; Use A:B as the shift left register and C as the shift right register; store partial product in SP+3:SP+4
    CLR     A          ; High byte of shift register (A:B) is 0
    LD      B, SP, 3   ; Low byte of shift register is multiplier, which is at location SP+3
    LD      C, SP, 4   ; C is the multiplicand, at location SP+4
    ST      A, SP, 3   ; Clear high byte in RAM
    ST      A, SP, 4   ; Clear low byte in RAM

    CLR     E
NextBitSP:
    CMP     C, E        ; C == 0?
    BEQ     DoneSP      ; If no more bits to multiply by then we're done

    RORC    C           ; Do we need to do an add?
    BCC     RotateABSP  ; If not then skip

    LD      D, SP, 4    ; Else we need to do the add, low byte first
    ADD     D, B, D
    ST      D, SP, 4
    LD      D, SP, 3    ; load the intermediate product (high byte)
    ADC     D, A, D     ; Add the high byte intermidiate product with the shifted high byte of multiplicand, plus any carry bit from previous add
    ST      D, SP, 3    ; Store high byte

RotateABSP:
    ROLC    B           ; Always rotate A:B
    ROLC    A           ; Shift the MSB of B in to A
    BRA     NextBitSP
DoneSP:
    RTS

.byte  multiply 2      ; Declare variable for multiplication
MultiplyPtr_Sub:
    ; [X:X+1] = [X] * [X+1]
	; Use A:B as the shift left register and C as the shift right register; store partial sum in X:X+1
    CLR     A          ; High byte of shift register (A:B) is 0
    LD      B, X, 0    ; Low byte of shift register is first number
    LD      C, X, 1    ; C is the other number to multiply by
    ST      A, X, 0    ; Clear high byte in RAM
    ST      A, X, 1    ; Clear low byte in RAM

    CLR     E
NextBit:
    CMP     C, E        ; C == 0?
    BEQ     Done        ; If no more bits to multiply by then we're done

    RORC    C           ; Do we need to do an add?
    BCC     RotateAB    ; If not then skip

    LD      D, X, 1     ; Else we need to do the add, low byte first
    ADD     D, B, D
    ST      D, X, 1
    LD      D, X, 0     ; load the intermediate sum (high byte)
    ADC     D, A, D     ; Add the high byte intermidiate sum with the shifted high byte of multiplicand, plus any carry bit from previous add
    ST      D, X, 0     ; Store high byte

RotateAB:
    ROLC    B           ; Always rotate A:B
    ROLC    A           ; Shift the MSB of B in to A
    BRA     NextBit
Done:
    RTS
