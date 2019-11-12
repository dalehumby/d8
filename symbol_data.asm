; Symbol resolution (recursive) for data and defines
; No forward resolution yet. All symbols muse be defined before they're used

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
	BEQ		0x0000
	LDD		A, fib
	LDI		B, VAL
	ADD		C, A, B
	INC		D, C
loop:
	LDD		B, array
	ADC		D, B, C
	MOV		C, D
	BRA		Start			; loop back to start
	BRA		loop

	STOP					; Halt
