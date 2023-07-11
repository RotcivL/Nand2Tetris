import os
import sys
from Parser import Parser
from Code import Code

"""Hack Assembler takes an assembly code and translates it into binary machine language"""
class HackAssembler:
    def __init__(self, file_path):
        """
        opens the assembly file discarding empty and comment lines and striping whitespace
        @param file_path(str): path to .asm file that is being translated to binary
        """
        self.instructions=[]
        self.binary=[]
        self.symbol_table = {
            "SP":0, "LCL":1, "ARG":2, "THIS":3, "THAT":4,
		    "R0":0, "R1":1, "R2":2, "R3":3, "R4":4, "R5":5,
            "R6":6, "R7":7, "R8":8, "R9":9, "R10":10, "R11":11,
		    "R12":12, "R13":13, "R14":14, "R15":15,
		    "SCREEN":16384, "KBD":24576
        } #default symbols in Hack
        self.next_var_address = 16 #first free memery address
        self.file_name = os.path.basename(file_path)
        ext = self.file_name[-3:]
        assert ext == "asm", "incorrect file type, input must be named like xxx.asm"
        with open(file_path,'r') as file:
            for line in file:
                line = line.strip()
                if not line or line[0] == '/':
                    continue
                if line.find('/') != -1:
                    line = line[:line.find('/')]
                self.instructions.append(line.strip())
        self.parser = Parser(self.instructions)
        self.code = Code()
        
    def symbol_check(self):
        """
        first pass to map all labels to the line count in file
        """
        check = Parser(self.instructions)
        line = -1
        while check.hasMoreLines():
            check.advance()
            type = check.instructionType()
            if type == 'L':
                self.symbol_table[check.symbol()] = line + 1
            else:
                line += 1
        

    def parse(self):
        """
        second pass through the assembly code
        converts assembly to binary line by line
        """
        while self.parser.hasMoreLines():
            self.parser.advance()
            type = self.parser.instructionType()
            binary_code = ""
            # A commands in Hack
            if type =='A':
                symbol = self.parser.symbol()
                if not symbol.isdecimal():
                    if symbol in self.symbol_table:
                        symbol = self.symbol_table[symbol]
                    else:
                        self.symbol_table[symbol] = self.next_var_address
                        symbol = self.next_var_address
                        self.next_var_address += 1
                symbol = format(int(symbol), 'b')
                pre = '0'*(16-len(symbol))
                binary_code += pre+symbol
            # skip line if it is a label (no neeed to convert to binary)
            elif type == 'L':
                continue
            # C commands in Hack
            else:
                dest = self.parser.dest()
                comp = self.parser.comp()
                jump = self.parser.jump()

                dest_code = self.code.dest(dest)
                comp_code = self.code.comp(comp)
                jump_code = self.code.jump(jump)
                binary_code += "111"+comp_code+dest_code+jump_code
            self.binary.append(binary_code)

    def create_binary(self):
        """
        creates the binary code file from the list of all 
        """
        binary_file_name = self.file_name[:-4]+".hack"
        with open(binary_file_name, 'w') as file:
            for line in self.binary:
                file.write(line+'\n')

def main():
    file_path=sys.argv[1]
    assembler = HackAssembler(file_path)
    assembler.symbol_check()
    assembler.parse()
    assembler.create_binary()

if __name__ == '__main__':
    main()