# Multiply 2 8-bit numbers together, resulting in a 16-bit number

.reset Start

Start:
	LDI		A, 5
	LDI		B, 3
	BSR		Multiply_Sub
	STOP

Multiply_Sub:
	ROLC	C, A
	MOV		A, C

	ROLC	D, B
	MOV		B, D

	BRA		Multiply_Sub

	RTS
