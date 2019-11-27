; Calculate the first 10 numbers in the Fibonacci sequence

.reset  Start
.define LENGTH  10
.data   fib     LENGTH

Start:
    ; Define the end condition
    LDI     D, &fib+LENGTH      

    ; Initialise the Fibonacci sequence
    LDI     X, &fib
    LDI     A, 0
    STX     A
    INCX
    LDI     B, 1
    STX     B
    INCX

Loop:
    ; Calcualte the next value in the sequence
    ADD     C, A, B
    STX     C
    INCX
    MOV     A, B
    MOV     B, C

    ; End yet?
    CMP     X, D
    BNE     Loop
    STOP
