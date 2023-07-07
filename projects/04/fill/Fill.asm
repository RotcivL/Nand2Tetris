// This file is part of www.nand2tetris.org
// and the book "The Elements of Computing Systems"
// by Nisan and Schocken, MIT Press.
// File name: projects/04/Fill.asm

// Runs an infinite loop that listens to the keyboard input.
// When a key is pressed (any key), the program blackens the screen,
// i.e. writes "black" in every pixel;
// the screen should remain fully black as long as the key is pressed. 
// When no key is pressed, the program clears the screen, i.e. writes
// "white" in every pixel;
// the screen should remain fully clear as long as no key is pressed.

// Pseudocode
// MAIN :
//     if (RAM[KBD] != 0) goto BLACK
//     else goto WHITE
// BLACK :
//     i = 0
//     start = RAM[SCREEN]
//     while i < 8192:
//        start = start + i
//        RAM[start+i] = -1
//        i = i + 1
//     GOTO MAIN
// WHITE :
//     i = 0
//     start = RAM[SCREEN]
//     while i < 8192:
//        start = start + i
//        RAM[start+i] = 0
//        i = i + 1
//     GOTO MAIN

  (MAIN)
    @KBD
    D=M
    @BLACK
    D; JNE
    @WHITE
    0; JMP

  (BLACK)
    @i
    M=0
    (LOOPBLACK)
      // if i >= 8192 goto MAIN
      @8192
      D=A
      @i
      D=D-M
      @MAIN
      D; JLE
      // turn 16 bit black starting from screen 
      @i
      D=M
      @SCREEN
      A=A+D
      M=-1
      // i = i + 1
      @i
      M=M+1
      // goto LOOPBLACK
      @LOOPBLACK
      0; JMP

  (WHITE)
    @i
    M=0
    (LOOPWHITE)
      // if i >= 8192 goto MAIN
      @8192
      D=A
      @i
      D=D-M
      @MAIN
      D; JLE
      // turn 16 bit white starting from screen 
      @i
      D=M
      @SCREEN
      A=A+D
      M=0
      // i = i + 1
      @i
      M=M+1
      // goto LOOPWHITE
      @LOOPWHITE
      0; JMP


    

