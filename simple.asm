; File with no defines, values, etc., just raw addresses

; Implicit code start at address 0x0000
; Data start at 0x00A0

LDI		A, 0
LDI		B, 5
ADD		C, A, B 		; C = A + B
STD		C, 0x00A0   	; Store C to address 0x00A0
CMP		A, B
BEQ		0x0000
LDD		A, 0x00A1
LDI		B, 0b00001111
ADD		C, A, B
INC		D, C
LDD		B, 0x00A0
ADC		D, B, C
MOV		C, D
BRA		0x0000			; loop back to start
BRA		0b1111
STOP					; Halt
