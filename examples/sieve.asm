; Implement Sieve of Eratosthenes

.reset 		Start

.define		LENGTH			100

.data		array			LENGTH
.data		nextAddress		1

.origin 	0x0100
Start:
	; First fill the array with 0..99 numbers
	LDI		X, &array
	LDI		A, 0

	LDI		C, &array+LENGTH		; End condition
	NOT		B, C 					; Make C negative for later compare, store in D
	INC		D, B

FillArray:
	STX		A
	INC		B, A
	MOV		A, B
	INCX
	CMP		X, C
	BNE		FillArray

	; Initialise the search
	LDI		A, 2
	LDI		B, &array
	ADD		X, A, B

NextSearch:
	; Store next position to search, leave X as current value
	INC		B, X
	STD		B, nextAddress

	; Start deleting multiples from the array
	LDI		C, 0 					; Deleted means 0 in array
DeleteNextMultiple:
	ADD		B, X, A 				; X = X + A
	MOV		X, B

	; Is index past the end of the array?
	ADD		B, X, D
	BCC		ExitDelete
	; Else mark Multiple as deleted (set to 0)
	STX		C 						; [X] = 0
	BRA		DeleteNextMultiple
ExitDelete:

	; Try next number in the list
	LDD		X, nextAddress
	LDX		A 						; A <- [X]
	BNE		NextSearch

	; If that number is 0 then it means that it's been eliminated.
	; Try the next one unitl you go past the end of the array
	LDI		C, &array+LENGTH		; End condition
	INCX
	CMP		X, C
	BNE		ExitDelete
	
	; Else reached the end of the array, so stop
	STOP
