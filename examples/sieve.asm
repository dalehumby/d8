; Implement Sieve of Eratosthenes
; https://en.wikipedia.org/wiki/Sieve_of_Eratosthenes
; Start with an array of numbers between 2..MAX, filter out all non-primes
; Left with an array like [2, 3, 0, 5, 0, 7, 0, 0, 0, 11, 0, 13, ..., 23]

.reset      Start
.define     MAX             23      ; Highest number to test
.define     LENGTH          MAX-1   ; Don't include 1 as the first prime

.origin     0x10
.byte       array           LENGTH
.byte       thisPrime       1

Start:
    LD      X, &array               ; Starting address
    LD      E, &array+LENGTH-1      ; End address
    LD      A, #2                   ; First prime

FillArray:                          ; First fill the array with 2..MAX
    ST      A, X, 0
    INC     A
    INC     X
    CMP     E, X
    BCC     FillArray               ; Fill array until X > E

    ; Initialise
    LD      X, &array-1             ; Back to start of array (FIXME hacky -1)
    ST      X, thisPrime
    CLR     B

TryNextPrime:
    LD      X, thisPrime
    INC     X
    CMP     E, X
    BCS     End                     ; If reach end of array then we're done
    ST      X, thisPrime
    LD      A, X, 0                 ; Load A with next potential prime
    CMP     A, B
    BEQ     TryNextPrime            ; array[X] == 0 which means not-a-prime, so try next number

FilterMultiples:
    ADD     X, X, A                 ; X = X + A
    CMP     E, X                    ; Past the end of the array?
    BCS     TryNextPrime            ; If so, go find the next prime
    ST      B, X, 0                 ; Else set array[X] = 0 to mark as not a prime
    BRA     FilterMultiples

End:
    STOP
