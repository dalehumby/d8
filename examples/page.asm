; Accessing variables, index and stack across page boundaries
.define     SPPS        0x0002  ; Location of the stack pointer page select memory mapped register

.reset      Start
.origin     0x0100
.byte       myVar       1
Start:
    CLR     PAGE
    LD      X, #0xFE
    LD      A, #0xAA
    ST      A, X, 0     ; 0x00FE <- 0xAA
    INC     X
    ST      A, X, 0     ; 0x00FF <- 0xAA
    INC     X           ; Notice X wrapped around to 0, PAGE register does not automatically increment
    ST      A, X, 0     ; 0x0000 <- 0xAA instead of 0x0100. Need to add a BCS and INC PAGE instructions
                        ;                to correctly identify an X wrap and increment the PAGE register

    LD      X, #0xFE
    LD      A, #0xBB
    ST      A, X, 0     ; 0x00FE <- 0xBB
    ST      A, X, 1     ; 0x00FF <- 0xBB
    ST      A, X, 2     ; 0x0100 <- 0xBB  Notice that in indirect addressing mode with an X offset 
                        ;                 the offset across a page boundary is correctly handled


    ; Stack pointer
    CLR     E
    ST      B, SPPS     ; set stack pointer page to 0
    LD      SP, #0xFF
    ; TODO ... same as with X, need to manually change the SPPS value in RAM
    ; but using an offset like works across page boundaries
    ST      A, SP, 2

    ; Direct addressing: If a variable is in another page
    LD      PAGE, &myVar >> 8       ; Change page based on high byte of myVar's address
    LD      A, myVar                ; then can load myVar in to register
    ; Try keep all variables in a single page, like page 0, the stack in another page, and the code in yet another page
    ; Try not to cross page boundaries

    STOP

