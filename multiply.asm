# Multiply 2 8-bit numbers together, resulting in a 16-bit number

.reset Start

Start:
	LDI		A, 5
	LDI		B, 3
	BSR		Multiply_Sub
	STOP

Multiply_Sub:
	; C:D = A * B (Use X as working memory)
	LDI		C, 0
	LDI		D, 0

NextBit:
	CMP		B, C		; B == 0?
	BEQ		Done		; If no more bits to multiply by then we're done

	RORC	X, B
	MOV		B, X
	BCC		NextBit

	ADD		X, A, D
	MOV		D, X

	ROLC	X, A
	BEQ		Done
	MOV		A, X
	BRA		NextBit
Done:
	RTS
