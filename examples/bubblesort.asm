; Implementation of bubble sort (Descending)
; https://en.wikipedia.org/wiki/Bubble_sort

.define     SPPS        0x0002      ; Stack pointer page select
.define     TOPSTACK    0x0F

.reset      Init

.origin     TOPSTACK+1
.array      mylist      { 5, 1, 4, 2, 8 }
Init:
    CLR     PAGE
    ST      PAGE, SPPS              ; Set PAGE and SPPS to page 0
    LD      SP, #0x0F               ; Set location of Stack pointer
    LD      C, &mylist+5-1          ; Ending address: Start address + length of array - 1, TODO sizeof(mylist)
    LD      D, #0                   ; Store what 'false' means
NextIteration:
    LD      X, &mylist              ; X is start address of array to sort
    LD      E, #0                   ; Swapped is false
NextPair:
    LD      A, X, 0
    LD      B, X, 1
    CMP     A, B
    BCC     Increment
    ST      A, X, 1                 ; Swap
    ST      B, X, 0
    LD      E, #1                   ; There was a swap
Increment:
    INC     X
    CMP     X, C
    BNE     NextPair                ; Continue checking pairs until end of list
    CMP     D, E
    BNE     NextIteration           ; If there was a swap then do another iteration
End:
    STOP
