; Calculate the first 10 numbers in the Fibonacci sequence

.define LENGTH  10

	LDI     A, 0
	LDI     B, 2
	OR      A, A, B

Start:
    LDI     PAGE, 1             ; change to page 1
    LDI     D, &fib+LENGTH      ; Define the end condition

    ; Initialise the Fibonacci sequence
    LDI     X, &fib
    LDI     A, 0
    STX     A
    INC     X, X
    LDI     B, 1
    STX     B
    INC     X, X

Loop:
    ; Calculate the next value in the sequence
    ADD     C, A, B
    STX     C
    INC     X, X
    MOV     A, B
    MOV     B, C

    ; End yet?
    CMP     X, D
    BNE     Loop
    STOP

; Data in Page 1
.origin 0x0100
.data   fib     LENGTH
