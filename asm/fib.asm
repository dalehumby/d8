; Calculate the first 10 numbers in the Fibonacci sequence

.define LENGTH  10

Init:
    LDI     SP, 0x0F            ; Set top of stack
    LDI     PAGE, 1             ; Set page

Start:
    LDI     D, &fib+LENGTH      ; Define the end condition

    ; Initialise the Fibonacci sequence
    LDI     X, &fib
    CLR     A
    STX     A, 0
    INC     X
    LDI     B, 1
    STX     B, 0
    INC     X

Loop:
    ; Calculate the next value in the sequence
    ADD     C, A, B
    STX     C, 0
    INC     X
    MOV     A, B
    MOV     B, C

    ; End yet?
    CMP     X, D
    BNE     Loop
    STOP

; Data in Page 1
.origin 0x0100
.data   fib     LENGTH
