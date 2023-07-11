""""
Parser that determines the type, symbol and sections of each
instruction in assembly code
"""
class Parser:
    def __init__(self, instructions):
        """
        sets the current location of parser
        @param instructions(list(str)): list of assembly instructions
        """
        self.instructions = instructions
        self.curr_instruction = -1
        self.curr_type = None

    def hasMoreLines(self):
        """
        checks if parser has reached the last instruction
        """
        return self.curr_instruction<len(self.instructions)-1

    def advance(self):
        """
        moves the current location to next instruction
        """
        self.curr_instruction += 1
        
    def instructionType(self):
        """
        sets the current instruction's type
        """
        if self.instructions[self.curr_instruction][0]=='@':
            self.curr_type = 'A'
        elif self.instructions[self.curr_instruction][0]=='(':
            self.curr_type = 'L'
        else:
            self.curr_type = 'C'
        return self.curr_type
            
    def symbol(self):
        """
        returns the symbol, label is type L and decimal/variable if type A
        """
        if self.curr_type == 'A':
            return self.instructions[self.curr_instruction][1:]
        else:
            return self.instructions[self.curr_instruction][1:-1]

    def dest(self):
        """
        returns the dest section of instruction
        """
        eq_pos = self.instructions[self.curr_instruction].find('=')
        if eq_pos == -1:
            return 'null'
        return self.instructions[self.curr_instruction][:eq_pos]
    
    def comp(self):
        """
        returns the comp section of instruction
        """
        eq_pos = self.instructions[self.curr_instruction].find('=')
        semi_pos = self.instructions[self.curr_instruction].find(';')
        if semi_pos == -1:
            if eq_pos == -1:
                return self.instructions[self.curr_instruction]
            return self.instructions[self.curr_instruction][eq_pos+1:]
        if eq_pos == -1:
            return self.instructions[self.curr_instruction][:semi_pos]
        return self.instructions[self.curr_instruction][eq_pos+1:semi_pos]
    
    def jump(self):
        """
        returns the jump section of instruction
        """
        semi_pos = self.instructions[self.curr_instruction].find(';')
        if semi_pos == -1:
            return 'null'
        return self.instructions[self.curr_instruction][semi_pos+1:]
    