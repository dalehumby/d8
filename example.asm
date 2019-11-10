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

.include "derivatives.inc"

.segment	Ram			0x0002 TO 0x00FF
.segment	Main		0x0100 TO 0xFFFF

.define Ram			 	0x0002		; Working memory between 02 and FF
.define Main	 		0x0100		; Where the main code starts
.reset  Start						; Define where code starts executing after rest

.origin Ram
.data i 		1	; 1 byte for i
.data temp 		2	; 2 bytes for temp, uninitialised
.data fibonacci 10 { 1, 2, 3, 4, 5, 6, 7, 8, 9, 0 }  ; 10 bytes for fibonacci, initialised 1 .. 0

.origin Main
Start:
	BSR		Add_Sub
	
	; fibonacci[0] = i++
	LDD		B, i
	INC		B
	STD		B, i
	BNE		Start
	
	LDD		X, &fibonacci		; Load the first bytes' address in to X
	STX		B 					; Store the value of B at address X: [X] <- B
	BRA		Start


; 16-bit counter
Add_Sub:
	LDD		A, temp+1	; increment the low byte
	INC		A
	STD		A, temp+1
	BCC		Return		; If did not cause an overflow then return
	LDD		A, temp		; if overflow then inc high byte
	INC		A
	STD		A, temp
Return:
	RTS
