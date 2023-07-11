""""
Code class that contains the mappings of all C command
assembly codes to their binary representation
"""
class Code:
    def __init__(self):
        """
        Initialise the mappings of assembly code to binary for C commands
        """
        self.dest_table={
		    "null":"000", "M":"001", "D":"010", "MD":"011",
		    "A":"100", "AM":"101", "AD":"110", "AMD":"111"
		}

        self.comp_table = {
            "0":"0101010", "1":"0111111", "-1":"0111010", 
            "D":"0001100", "A":"0110000", "M":"1110000",
            "!D":"0001101", "!A":"0110001", "!M":"1110001",
            "-D":"0001111", "-A":"0110011", "-M":"1110011",
            "D+1":"0011111", "A+1":"0110111", "M+1":"1110111",
            "D-1":"0001110", "A-1":"0110010", "M-1":"1110010",
            "D+A":"0000010", "D+M":"1000010", "D-A":"0010011",
            "D-M":"1010011", "A-D":"0000111", "M-D":"1000111",
            "D&A":"0000000", "D&M":"1000000", "D|A":"0010101",
            "D|M":"1010101"
        }

        self.jump_table={
		    "null":"000","JGT":"001","JEQ":"010","JGE":"011",
		    "JLT":"100","JNE":"101","JLE":"110","JMP":"111"
		}


    def dest(self, code):
        """
        returns corresponding dest binary from assembly code
        @param code(str): assembly representation of dest in Hack C command
        """
        return self.dest_table[code]
    
    def comp(self, code):
        """
        returns corresponding comp binary from assembly code
        @param code(str): assembly representation of comp in Hack C command
        """
        return self.comp_table[code]
    
    def jump(self, code):
        """
        returns corresponding jump binary from assembly code
        @param code(str): assembly representation of jump in Hack C command
        """
        return self.jump_table[code]