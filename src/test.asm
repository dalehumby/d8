; This is a comment

.define     LENGTH      10
.define     TOPSTACK    0xFF

.reset Start

; Begin here
.origin TOPSTACK+1
Start:
    NOP
    BRA     Start

.string helloStr "Hello WORLD"
