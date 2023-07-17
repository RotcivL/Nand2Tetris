import os
import sys


class Parser:
    """
    Hack vm file parser
    Loads the supplied vm file, parsing each line of code.
    """

    def __init__(self, file_path):
        """
        Opens file discarding empty and comment lines and stripping wehitespace.
        @param file_path(str): path to .vm file that is being translated to assembly
        """
        self.commands = []
        self.curr_line = -1
        self.curr_command = None

        with open(file_path, "r") as file:
            for line in file:
                line = line.partition("//")[0]
                line = line.strip()
                if line:
                    self.commands.append(line)

    def hasMoreCommands(self):
        """
        checks to see if parser has reached last command
        """
        return self.curr_line < len(self.commands) - 1

    def advance(self):
        """
        moves the current location to next command
        """
        self.curr_line += 1
        self.curr_command = self.commands[self.curr_line]

    def commandType(self):
        """
        returns the current command's type
        """
        commands = self.curr_command.split(" ")

        if len(commands) == 1:
            return "C_ARITHMETIC"
        elif commands[0] == "pop":
            return "C_POP"
        elif commands[0] == "push":
            return "C_PUSH"

    def arg1(self):
        """
        returns the command itself if the current command is an arithmetic command
        returns the segment for push and pop commands
        """
        if self.commandType() == "C_ARITHMETIC":
            return self.curr_command.split(" ")[0]
        else:
            return self.curr_command.split(" ")[1]

    def arg2(self):
        """
        returns the index for push and pop commands
        """
        return self.curr_command.split(" ")[2]


class CodeWriter:
    """
    translates assembly instruction from vm command and write to an output file
    """

    def __init__(self, file_path):
        """
        sets up the output file
        """
        self.file = open(file_path, "w")
        self.file_name = os.path.basename(file_path)[:-4]

        # assembly instruction for each vm command
        self.arithmetic_logical_commands = {
            "add": "M=M+D",
            "sub": "M=M-D",
            "neg": "M=-M",
            "eq": "D;JEQ",
            "gt": "D;JGT",
            "lt": "D;JLT",
            "and": "M=D&M",
            "or": "M=D|M",
            "not": "M=!M",
        }
        # map of vm segment names to assembly symbols
        self.segment_table = {
            "local": "@LCL",
            "argument": "@ARG",
            "this": "@THIS",
            "that": "@THAT",
            "pointer": "@3",
            "temp": "@5",
        }
        self.label_index = 0

    def writeArithmetic(self, command):
        """
        writes assembly instruction for vm arithmetic commands
        """
        asm_code = []
        if command in ["neg", "not"]:
            asm_code += ["@SP", "A=M-1", self.arithmetic_logical_commands[command]]
        elif command in ["add", "sub", "and", "or"]:
            asm_code += [
                "@SP",
                "AM=M-1",
                "D=M",
                "A=A-1",
                self.arithmetic_logical_commands[command],
            ]
        elif command in ["eq", "gt", "lt"]:
            label = command + "_" + str(self.label_index)
            self.label_index += 1
            asm_code += [
                "@SP",
                "AM=M-1",
                "D=M",
                "A=A-1",
                "D=M-D",
                "M=-1",
                "@" + label,
                self.arithmetic_logical_commands[command],
                "@SP",
                "A=M-1",
                "M=0",
                "(" + label + ")",
            ]
        for line in asm_code:
            self.file.write(line + "\n")

    def writePushPop(self, command, segment, index):
        """
        writes assembly instructions for push pop commands
        """
        asm_code = []
        if command == "C_PUSH":
            if segment in ["local", "argument", "this", "that"]:
                asm_code = [
                    self.segment_table[segment],
                    "D=M",
                    "@" + index,
                    "A=A+D",
                    "D=M",
                ]
            elif segment in ["temp", "pointer"]:
                asm_code = [
                    self.segment_table[segment],
                    "D=A",
                    "@" + index,
                    "A=A+D",
                    "D=M",
                ]
            elif segment == "constant":
                asm_code = ["@" + index, "D=A"]
            elif segment == "static":
                asm_code = ["@" + self.file_name + "." + index, "D=M"]
            asm_code += ["@SP", "AM=M+1", "A=A-1", "M=D"]

        elif command == "C_POP":
            if segment == "static":
                asm_code += ["@" + self.file_name + "." + index, "D=M", "@R13", "M=D"]
            elif segment in ["local", "argument", "this", "that"]:
                asm_code += [
                    self.segment_table[segment],
                    "D=A",
                    "@" + index,
                    "D=A+D",
                    "@R13",
                    "M=D",
                ]
            elif segment in ["temp", "pointer"]:
                asm_code += [
                    self.segment_table[segment],
                    "D=A",
                    "@" + index,
                    "D=A+D",
                    "@R13",
                    "M=D",
                ]
            asm_code += ["@SP", "AM=M-1", "D=M", "@R13", "A=M", "M=D"]

        for line in asm_code:
            self.file.write(line + "\n")

    def close(self):
        self.file.close()


def main():
    """
    Main class to translate vm file to asm file.
    """
    # geting and checking file validity
    file_path = sys.argv[1]
    ext = file_path[-2:]
    assert ext == "vm", "incorrect file type, input must be named like xxx.vm"

    # Create parser object
    parser = Parser(file_path)

    # create codewriter object
    asm_file_name = file_path[:-3] + ".asm"
    writer = CodeWriter(asm_file_name)

    # main loop to iterate through commands line by line, writing the corresponding assembly commands to the output file
    while parser.hasMoreCommands():
        parser.advance()
        type = parser.commandType()
        if type == "C_ARITHMETIC":
            writer.writeArithmetic(parser.arg1())
        else:
            writer.writePushPop(type, parser.arg1(), parser.arg2())

    writer.close()


if __name__ == "__main__":
    main()
