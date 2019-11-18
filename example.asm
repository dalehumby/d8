; Test example file
; These programs arent supposed to make sense, only test the assembler
;*******************************************************************************************
; STYLE GUIDE
; DEFINES, MACROS and ASSEMBLER OPCODES (LDA)
; , space; space around +-*/
; Jump points are PascalCase: MainLoop
; Subroutines are PascalCase with _Sub postfix: StreamBytes_Sub
; Variables are camelCase: dataBufferAddress
; Opcode in col 9, operands in col 17, comments col 41 (or at least aligned in that block of code.)
;*******************************************************************************************

;.include "derivatives.inc" ; Not yet supported
;.segment	Ram			0x0002 TO 0x00FF
;.segment	Main		0x0100 TO 0xFFFF

.define Ram			 	0x0002		; Working memory between 02 and FF
.define Main	 		0x0100		; Where the main code starts
.define LENGTH			5
.reset  Start						; Define where code starts executing after rest

.origin Ram
.data i 		1	; 1 byte for i
.data temp 		2	; 2 bytes for temp, uninitialised
.data fibonacci 10 { 1, 2, 3, 4, 5, 6, 7, 8, 9, 0 }  ; 10 bytes for fibonacci, initialised 1 .. 0

.origin Main
Start:
	LDI		A, 0xFE
	STD		A, temp+1
Start2:
	BSR		Add_Sub
	
	; fibonacci[0] = i++
	LDD		B, i
	INC		C, B
	STD		C, i
	DEC		D, C
	BNE		Start2
	
	LDI		X, &fibonacci		; Load the first bytes' address in to X
	STX		B 					; Store the value of B at address X: [X] <- B
	BRA		Start


; 16-bit counter
Add_Sub:
	LDD		A, temp+1	; increment the low byte
	INC		B, A
	STD		B, temp+1
	BCC		Return		; If did not cause an overflow then return
	LDD		A, temp		; if overflow then inc high byte
	INC		B, A
	STD		B, temp
Return:
	LDD		C, temp+LENGTH
	RTS

	STOP				; Incase we ever get here
