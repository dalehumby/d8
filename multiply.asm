; Multiply 2 8-bit numbers together, resulting in a 16-bit number

.reset Start
.data  multiply 2
.data  SPCHtemp 1  ; used to temporarily hold the SPCH

Start:
    LDI     A, 2
    STD     A, multiply
    LDI     A, 0xFF
    STD     A, multiply+1
    LDI     X, &multiply     ; load X with the pointer in memory for what want to multiply
    BSR     Multiply_Sub
    STOP

Multiply_Sub:
    ; [X:X+1] = [X] * [X+1]
    STD     SPCH, SPCHtemp  ; Save the return address
    MOV     SPCH, X         
    
    LDI     A, 0       ; High byte of shift register (A:B) is 0
    LDX     B          ; Low byte of shift register is B
    STX     A          ; Clear the high byte in RAM
    INC     X, X       ; Select low byte
    LDX     C
    STX     A          ; Clear low byte in RAM

NextBit:
    LDI     D, 0
    CMP     C, D        ; C == 0?
    BEQ     Done        ; If no more bits to multiply by then we're done

    RORC    C, C        ; Do we need to do an add?
    BCC     RotateAB    ; If not then skip

    LDX     D           ; Else we need to do the add, low byte first
    ADD     D, B, D
    STX     D
    MOV     X, SPCH     ; Load pointer to high byte in to X
    LDX     D           ; load the intermediate sum (high byte)
    ADC     D, A, D     ; Add the high byte intermidiate sum with the shifted high byte of multiplicand, plus any carry bit from previous add
    STX     D           ; Store high byte
    INC     X, X        ; Put pointer back to low byte

RotateAB:
    ROLC    B, B        ; Always rotate A:B
    ROLC    A, A        ; Shift the MSB of B in to A
    BRA     NextBit
Done:
    LDD     SPCH, SPCHtemp
    RTS
