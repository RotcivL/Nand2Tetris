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
            if commands[0] == "return":
                return "C_RETURN"
            else:
                return "C_ARITHMETIC"
        elif commands[0] == "pop":
            return "C_POP"
        elif commands[0] == "push":
            return "C_PUSH"
        elif commands[0] == "label":
            return "C_LABEL"
        elif commands[0] == "goto":
            return "C_GOTO"
        elif commands[0] == "if-goto":
            return "C_IF"
        elif commands[0] == "function":
            return "C_FUNCTION"
        elif commands[0] == "call":
            return "C_CALL"

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
        returns the index for push/pop/call/function commands
        """
        return int(self.curr_command.split(" ")[2])


class CodeWriter:
    """
    translates assembly instruction from vm command and write to an output file
    """

    def __init__(self, file_path):
        """
        sets up the output file
        """
        self.file = open(file_path, "w")
        self.file_name = ""
        self.function_name = ""

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
        self.return_index = 0

        # VM bootstrap
        asm_code = ["@256", "D=A", "@SP", "M=D"]
        for line in asm_code:
            self.file.write(line + "\n")
        self.writeCall("Sys.init", 0)

    def setFileName(self, file_name):
        """
        sets the file name for static varaible labels
        """
        self.file_name = os.path.basename(file_name)[:-3]

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
        str_index = str(index)
        if command == "C_PUSH":
            if segment in ["local", "argument", "this", "that"]:
                asm_code = [
                    self.segment_table[segment],
                    "D=M",
                    "@" + str_index,
                    "A=A+D",
                    "D=M",
                ]
            elif segment in ["temp", "pointer"]:
                asm_code = [
                    self.segment_table[segment],
                    "D=A",
                    "@" + str_index,
                    "A=A+D",
                    "D=M",
                ]
            elif segment == "constant":
                asm_code = ["@" + str_index, "D=A"]
            elif segment == "static":
                asm_code = ["@" + self.file_name + "." + str_index, "D=M"]
            asm_code += ["@SP", "AM=M+1", "A=A-1", "M=D"]

        elif command == "C_POP":
            if segment == "static":
                asm_code += [
                    "@" + self.file_name + "." + str_index,
                    "D=A",
                    "@R13",
                    "M=D",
                ]
            elif segment in ["local", "argument", "this", "that"]:
                asm_code += [
                    self.segment_table[segment],
                    "D=M",
                    "@" + str_index,
                    "D=A+D",
                    "@R13",
                    "M=D",
                ]
            elif segment in ["temp", "pointer"]:
                asm_code += [
                    self.segment_table[segment],
                    "D=A",
                    "@" + str_index,
                    "D=A+D",
                    "@R13",
                    "M=D",
                ]
            asm_code += ["@SP", "AM=M-1", "D=M", "@R13", "A=M", "M=D"]

        for line in asm_code:
            self.file.write(line + "\n")

    def writeLabel(self, label):
        """
        writes assembly labels for branching
        for file xxx, function foo, label bar, label is formatted as xxx.foo$bar
        """
        label_name = self.function_name + "$" + label
        self.file.write("(" + label_name + ")\n")

    def writeGoto(self, label):
        """
        writes assembly to jump to specified label
        """
        label_name = self.function_name + "$" + label
        asm_code = ["@" + label_name, "0;JMP"]
        for line in asm_code:
            self.file.write(line + "\n")

    def writeIf(self, label):
        """
        writes assembly to jump to label if condition is met
        """
        label_name = self.function_name + "$" + label
        asm_code = ["@SP", "AM=M-1", "D=M", "@" + label_name, "D;JNE"]
        for line in asm_code:
            self.file.write(line + "\n")

    def writeFunction(self, function_name, n_args):
        """
        write assembly function label to declare function
        for file xxx, function foo, label is formateed as xxx.foo
        writes assembly to set n local variables to 0
        """
        self.function_name = function_name
        self.file.write("(" + function_name + ")\n")
        for _ in range(n_args):
            asm_code = ["@SP", "AM=M+1", "A=A-1", "M=0"]
            for line in asm_code:
                self.file.write(line + "\n")

    def writeCall(self, function_name, n_args):
        """
        write assembly code to call a function with n args
        assembly to save frame of caller
        """
        return_address = function_name + "$ret" + str(self.return_index)
        self.return_index += 1
        push_D = ["@SP", "AM=M+1", "A=A-1", "M=D"]
        asm_code = ["@" + return_address, "D=A"] + push_D  # push return_address
        for segment in ["LCL", "ARG", "THIS", "THAT"]:
            asm_code += ["@" + segment, "D=M"] + push_D  # push LCL, ARG, THIS, THAT
        asm_code += [
            "@SP",
            "D=M",
            "@" + str(n_args + 5),
            "D=D-A",
            "@ARG",
            "M=D",
        ]  # ARG = SP_5-n_args
        asm_code += ["@SP", "D=M", "@LCL", "M=D"]  # LCL = SP
        asm_code += ["@" + function_name, "0;JMP"]  # GOTO function
        asm_code += ["(" + return_address + ")"]  # return_address label
        for line in asm_code:
            self.file.write(line + "\n")

    def writeReturn(self):
        """
        write assembly to return to caller from callee after function is complete
        cleans up by saving return address so it can goto it later
        pushes the output into the stack
        restores the frame of the caller
        goto the return address it has saved
        """
        asm_code = ["@LCL", "D=M", "@R13", "M=D"]  # frame = LCL in R13
        asm_code += [
            "@5",
            "A=D-A",
            "D=M",
            "@R14",
            "M=D",
        ]  # return_address = *(frame-5) in R14
        asm_code += ["@SP", "AM=M-1", "D=M", "@ARG", "A=M", "M=D"]  # *ARG = pop()
        asm_code += ["@ARG", "D=M+1", "@SP", "M=D"]  # SP = ARG+1
        for segment in ["THAT", "THIS", "ARG", "LCL"]:
            asm_code += [
                "@R13",
                "AM=M-1",
                "D=M",
                "@" + segment,
                "M=D",
            ]  # restore THAT, THIS, ARG, LCL
        asm_code += ["@R14", "A=M", "0;JMP"]  # goto return_address
        for line in asm_code:
            self.file.write(line + "\n")

    def close(self):
        self.file.close()


def main():
    """
    Main class to translate vm file to asm file.
    """
    # geting and checking file validity
    files = []
    path = sys.argv[1]
    asm_file_name = None

    # check if it is a file
    if os.path.isfile(path):
        ext = path[-2:]
        assert ext == "vm", "incorrect file type, input must be named like xxx.vm"
        asm_file_name = path[:-3] + ".asm"
        files = [path]
    # check if it is a directory
    elif os.path.isdir(path):
        for file in os.listdir(path):
            # store all vm files to be parsed
            if file[-3:] == ".vm":
                files.append(os.path.join(path, file))
        # get the directory base name to be used as the asm file name
        path = path[:-1] if path[-1] == "/" else path
        asm_file_name = os.path.join(path, os.path.basename(path)) + ".asm"

    # create codewriter object
    writer = CodeWriter(asm_file_name)

    for file in files:
        writer.setFileName(file)
        parser = Parser(file)
        # main loop to iterate through commands line by line, writing the corresponding assembly commands to the output file
        while parser.hasMoreCommands():
            parser.advance()
            type = parser.commandType()
            if type == "C_ARITHMETIC":
                writer.writeArithmetic(parser.arg1())
            elif type in ["C_PUSH", "C_POP"]:
                writer.writePushPop(type, parser.arg1(), parser.arg2())
            elif type == "C_LABEL":
                writer.writeLabel(parser.arg1())
            elif type == "C_GOTO":
                writer.writeGoto(parser.arg1())
            elif type == "C_IF":
                writer.writeIf(parser.arg1())
            elif type == "C_FUNCTION":
                writer.writeFunction(parser.arg1(), parser.arg2())
            elif type == "C_CALL":
                writer.writeCall(parser.arg1(), parser.arg2())
            elif type == "C_RETURN":
                writer.writeReturn()

    writer.close()


if __name__ == "__main__":
    main()
