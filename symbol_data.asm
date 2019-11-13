; Symbol resolution (recursive) for data and defines
; Basic 2-pass assembler. 
; Defines must be defined first, then data and then code. 
; - Defines and Data use backward ref only.
; - Code can have fwd and back refs
; NOTE: This code doesnt do anything, just check my assembler

.define 	LENGTH 	2 ; comment on the define
.define 	VAL 	0b00001010

.data 		temp	LENGTH  ; temp is a length
.data 		fib 	0x03
.data 		array 	5 {1,2,3, 4, 5}

Start:  					; start of main program
	LDI		A, 0
	LDI		B, 5
	ADD		C, A, B 		; C = A + B
	STD		C, temp		   	; Store C to address 0x00A0
	CMP		A, B
	BEQ		0x0000			; Branch to address (not use symbol)
	BCC		loop			; forward branch
	LDD		A, fib
	LDI		B, VAL
	ADD		C, A, B
	INC		D, C
loop:
loop2:
	LDD		B, array
	ADC		D, B, C
	MOV		C, D
	BRA		Start			; loop back to start
	BRA		loop			; backwards branch

	STOP					; Halt
