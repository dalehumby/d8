; Implementation of bubble sort

.define     SPPS        0x0002      ; Stack pointer page select
.define     TOPSTACK    0x0F

.reset Init

.origin TOPSTACK+1
.array mylist { 5, 1, 4, 2, 8 }
Init:
    CLR     PAGE
    ST      PAGE, SPPS              ; Set PAGE and SPPS to page 0
    LD      SP, #0x0F               ; Set location of Stack pointer
    LD      X, &mylist
Next:

End:
    STOP
