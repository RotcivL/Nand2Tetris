import os
import sys

class JackTokens:
    def __init__(self, type, token):
        self.type = type
        self.token = token
        self.XMLSpecial = {'<':'&lt;', '>':'&gt;', '&':'&amp;', '"':'&quot;'}

    def xml(self):
        tag = None
        token = self.token
        if self.type == 'KEYWORD':
            tag = 'keyword'
        elif self.type == 'SYMBOL':
            tag = 'symbol'
            if self.token in self.XMLSpecial:
                token = self.XMLSpecial[self.token]
        elif self.type == 'IDENTIFIER':
            tag = 'identifier'
        elif self.type == 'INT_CONST':
            tag = 'integerConstant'
        elif self.type == 'STRING_CONST':
            tag = 'stringConstant'
        return '<'+tag+'> '+token+' </'+tag+'>'
    
class JackTokenizer:
    def __init__(self, file):
        self.symbols = ['(', ')', '[', ']', '{', '}',
                        ',', ';', '=', '.', 
                        '+', '-', '*', '/', '&', '|', '~', '<', '>']
        self.keywords = ['class', 'constructor', 'function', 
		                'method', 'field', 'static', 'var', 'int', 'char',
		                'boolean', 'void', 'true', 'false', 'null', 'this',
		                'let', 'do', 'if', 'else', 'while', 'return']
        self.tokens = []

        with open(file, "r") as file:
            in_comment = False
            for line in file:
                if in_comment:
                    if '*/' in line:
                        line = line.partition('*/')[2]
                        in_comment = False
                    else: continue
                line = line.partition("//")[0]
                if "/*" in line:
                    if '*/' in line:
                        line = line.partition("/*")[0] + line.partition('*/')[2]
                    else:
                        line = line.partition("/*")[0]
                        in_comment = True
                self.processLine(line)

        self.current_pos = -1
        self.current_token = None
    
    def processLine(self, line):
        if '\"' in line:
            start = line.find('\"')
            end = line.find('\"', start+1)
            string = line[start:end+1]
            full = line[:start].split() + [string] + line[end+1:].split()
            for string in full:
                self.tokenize(string)
        else:
            line = line.split()
            for string in line:
                self.tokenize(string)

    def tokenize(self, string):
        if not string:
            return
        
        if string[0] in self.symbols:
            self.tokens.append(JackTokens('SYMBOL', string[0]))
            self.tokenize(string[1:])
        elif string[0] == '\"':
            self.tokens.append(JackTokens('STRING_CONST', string[1:-1]))
        elif string[0].isdecimal():
            i = 1
            while string[i].isdecimal():
                i += 1
            token = string[:i]
            self.tokens.append(JackTokens('INT_CONST', token))
            self.tokenize(string[i:])
        else:
            i = 0
            while i < len(string) and string[i] not in self.symbols:
                i += 1
            token = string[:i]
            if token in self.keywords:
                self.tokens.append(JackTokens('KEYWORD', token))
            else:
                self.tokens.append(JackTokens('IDENTIFIER', token))
            self.tokenize(string[i:])

        
    def hasMoreTokens(self):
        return self.current_pos < len(self.tokens) - 1

    def advance(self):
        self.current_pos += 1
        self.current_token = self.tokens[self.current_pos]

    def tokenType(self):
        return self.current_token.type

    def keyWord(self):
        return self.current_token.token

    def symbol(self):
        return self.current_token.token

    def identifier(self):
        return self.current_token.token

    def intVal(self):
        return int (self.current_token.token)

    def stringVal(self):
        return self.current_token.token

    def writeXML(self, file_name):
        with open(file_name, 'w') as file:
            file.write('<tokens>\n')
            for token in self.tokens:
                file.write(token.xml()+'\n')
            file.write('</tokens>\n')

def main():
    files = []
    path = sys.argv[1]
    xml_file_name = None
    # check if it is a file
    if os.path.isfile(path):
        ext = path[-5:]
        assert ext == ".jack", "incorrect file type, input must be named like xxx.jack"
        files = [path]
    # check if it is a directory
    elif os.path.isdir(path):
        for file in os.listdir(path):
            # store all vm files to be parsed
            if file[-5:] == ".jack":
                files.append(os.path.join(path, file))
        # get the directory base name to be used as the asm file name
        path = path[:-1] if path[-1] == "/" else path

    for file in files:
        xml_file_name = file[:-5] + "Token.xml"
        tokenizer = JackTokenizer(file)
        tokenizer.writeXML(xml_file_name)

if __name__ == "__main__":
    main()