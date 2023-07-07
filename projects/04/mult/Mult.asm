// This file is part of www.nand2tetris.org
// and the book "The Elements of Computing Systems"
// by Nisan and Schocken, MIT Press.
// File name: projects/04/Mult.asm

// Multiplies R0 and R1 and stores the result in R2.
// (R0, R1, R2 refer to RAM[0], RAM[1], and RAM[2], respectively.)
//
// This program only needs to handle arguments that satisfy
// R0 >= 0, R1 >= 0, and R0*R1 < 32768.

// Pseudocode
// i = 1
// total = 0
// LOOP : 
//      if (i > R0) goto STOP
//      total = total + R1
//      i = i + 1
//      goto LOOP
// STOP : 
//      R2 = total

    //init variables
    @i
    M=1
    @total
    M=0

  (LOOP)
    // if (i > R0) goto STOP
    @i
    D=M
    @R0
    D=D-M 
    @STOP
    D; JGT
    // total = total + R1
    @R1
    D=M
    @total
    M=M+D
    // i = i + 1
    @i
    M=M+1
    // goto LOOP
    @LOOP
    0; JMP
  (STOP)
    @total
    D=M
    @R2
    M=D
  (END)
    @END
    0; JMP   