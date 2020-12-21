; Calculate the first 10 numbers in the Fibonacci sequence

.define LENGTH  10

Init:
    LD      SP, #0x0F           ; Set top of stack
    LD      PAGE, #1            ; Set page

Start:
    LD      D, &fib+LENGTH      ; Define the end condition

    ; Initialise the Fibonacci sequence
    LD      X, &fib
    CLR     A
    ST      A, X, 0
    INC     X
    LD      B, #1
    ST      B, X, 0
    INC     X

Loop:
    ; Calculate the next value in the sequence
    ADD     C, A, B
    ST      C, X, 0
    INC     X
    MOV     A, B
    MOV     B, C

    ; End yet?
    CMP     X, D
    BNE     Loop
    STOP

; Data in Page 1
.origin 0x0100
.byte   fib     LENGTH
