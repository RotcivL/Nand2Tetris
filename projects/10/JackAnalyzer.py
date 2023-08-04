import os
import sys

class JackTokens:
    def __init__(self, type, token):
        self.type = type
        self.token = token
    
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

class CompliationEngine:
    def __init__(self, file):
        self.tokenizer = JackTokenizer(file) 
        self.indentation = 0
        self.classVarDec = ['static', 'field']
        self.subroutineDec = ['constructor', 'function', 'method']
        self.op = ['+', '-', '*', '/', '&', '|', '<', '>', '=']
        self.unary = ['~', '-']
        self.XMLentity = {'<':'&lt;', '>':'&gt;', '&':'&amp;', '"':'&quot;'}
        self.file = open(file[:-5] + "Compile.xml", "w")
        
    def compileClass(self):
        self.file.write('<class>\n')
        self.indentation += 1
        self.tokenizer.advance() 
        self.writeXML() # class
        self.tokenizer.advance() 
        self.writeXML() # className
        self.tokenizer.advance() 
        self.writeXML() # {
        # classVar or subroutine
        self.tokenizer.advance()
        while self.tokenizer.keyWord() in self.classVarDec:
            self.compileClassVarDec()
        while self.tokenizer.keyWord() in self.subroutineDec:
            self.compileSubroutine()
        
        self.writeXML() # }
        self.indentation -= 1
        self.file.write('</class>\n')
        self.file.close()

    def compileClassVarDec(self):
        self.file.write('  ' * self.indentation + '<classVarDec>\n')
        self.indentation += 1
        self.writeXML() # static | field 
        self.tokenizer.advance() 
        self.writeXML() # type
        self.tokenizer.advance() 
        self.writeXML() # varName
        self.tokenizer.advance()
        while self.tokenizer.symbol() == ',':
            self.writeXML() # ,
            self.tokenizer.advance() 
            self.writeXML() # varName
            self.tokenizer.advance()
        self.writeXML() # ;
        self.tokenizer.advance()
        self.indentation -= 1
        self.file.write('  ' * self.indentation + '</classVarDec>\n')


    def compileSubroutine(self):
        self.file.write('  ' * self.indentation + '<subroutineDec>\n')
        self.indentation += 1
        self.writeXML() # constructor | function | method
        self.tokenizer.advance()
        self.writeXML() # type
        self.tokenizer.advance()
        self.writeXML() # subroutineName
        self.tokenizer.advance()
        self.writeXML() # (
        self.compileParameterList()
        self.writeXML() # )
        self.compileSubroutineBody()
        self.tokenizer.advance()
        self.indentation -= 1
        self.file.write('  ' * self.indentation + '</subroutineDec>\n')


    def compileParameterList(self):
        self.file.write('  ' * self.indentation + '<parameterList>\n')
        self.indentation += 1
        self.tokenizer.advance()
        while self.tokenizer.tokenType() != 'SYMBOL':
            self.writeXML() # type
            self.tokenizer.advance()
            self.writeXML() # varName
            self.tokenizer.advance()
            if self.tokenizer.symbol() == ',':
                self.writeXML() # ,
                self.tokenizer.advance() 
        self.indentation -= 1
        self.file.write('  ' * self.indentation + '</parameterList>\n')

    def compileSubroutineBody(self):
        self.file.write('  ' * self.indentation + '<subroutineBody>\n')
        self.indentation += 1
        self.tokenizer.advance()
        self.writeXML() # {
        self.tokenizer.advance()
        while self.tokenizer.keyWord() == 'var':
            self.compileVarDec()

        self.compileStatements()
        self.writeXML() # }
        self.indentation -= 1
        self.file.write('  ' * self.indentation + '</subroutineBody>\n')

    def compileVarDec(self):
        self.file.write('  ' * self.indentation + '<varDec>\n')
        self.indentation += 1
        self.writeXML() # var
        self.tokenizer.advance() 
        self.writeXML() # type
        self.tokenizer.advance() 
        self.writeXML() # varName
        self.tokenizer.advance()
        while self.tokenizer.symbol() == ',':
            self.writeXML() # ,
            self.tokenizer.advance() 
            self.writeXML() # varName
            self.tokenizer.advance()
        self.writeXML() # ;
        self.tokenizer.advance()
        self.indentation -= 1
        self.file.write('  ' * self.indentation + '</varDec>\n')        

    def compileStatements(self):
        self.file.write('  ' * self.indentation + '<statements>\n')
        self.indentation += 1
        while self.tokenizer.tokenType() == 'KEYWORD':
            if self.tokenizer.keyWord() == 'let':
                self.compilelet()
            elif self.tokenizer.keyWord() == 'if':
                self.compileIf()
            elif self.tokenizer.keyWord() == 'while':
                self.compileWhile()
            elif self.tokenizer.keyWord() == 'do':
                self.compileDo()
            elif self.tokenizer.keyWord() == 'return':
                self.compileReturn()
        self.indentation -= 1
        self.file.write('  ' * self.indentation + '</statements>\n')

    def compilelet(self):
        self.file.write('  ' * self.indentation + '<letStatement>\n')
        self.indentation += 1
        self.writeXML() # let
        self.tokenizer.advance()
        self.writeXML() # varName
        self.tokenizer.advance()
        if self.tokenizer.symbol() == '[':
            self.writeXML() # [
            self.tokenizer.advance()
            self.compileExpression()
            self.writeXML() # ]
            self.tokenizer.advance()
        self.writeXML() # =
        self.tokenizer.advance()
        self.compileExpression()
        self.writeXML() # ;
        self.tokenizer.advance()
        self.indentation -= 1
        self.file.write('  ' * self.indentation + '</letStatement>\n')


    def compileIf(self):
        self.file.write('  ' * self.indentation + '<ifStatement>\n')
        self.indentation += 1
        self.writeXML() # if
        self.tokenizer.advance()
        self.writeXML() # (
        self.tokenizer.advance()
        self.compileExpression()
        self.writeXML() # )
        self.tokenizer.advance()
        self.writeXML() # {
        self.tokenizer.advance()
        self.compileStatements()
        self.writeXML() # }
        self.tokenizer.advance()
        if self.tokenizer.tokenType() == 'KEYWORD' and self.tokenizer.keyWord() == 'else':
            self.writeXML() # else
            self.tokenizer.advance()
            self.writeXML() # {
            self.tokenizer.advance()
            self.compileStatements()
            self.writeXML() # }
            self.tokenizer.advance()
        self.indentation -= 1
        self.file.write('  ' * self.indentation + '</ifStatement>\n')

    def compileWhile(self):
        self.file.write('  ' * self.indentation + '<whileStatement>\n')
        self.indentation += 1
        self.writeXML() # while
        self.tokenizer.advance()
        self.writeXML() # (
        self.tokenizer.advance()
        self.compileExpression()
        self.writeXML() # )
        self.tokenizer.advance()
        self.writeXML() # {
        self.tokenizer.advance()
        self.compileStatements()
        self.writeXML() # }
        self.tokenizer.advance()
        self.indentation -= 1
        self.file.write('  ' * self.indentation + '</whileStatement>\n')        

    def compileDo(self):
        self.file.write('  ' * self.indentation + '<doStatement>\n')
        self.indentation += 1
        self.writeXML() # do
        self.tokenizer.advance()
        # subroutinecall
        self.writeXML() # subroutineName | (className | varName)
        self.tokenizer.advance()
        if self.tokenizer.tokenType() == 'SYMBOL' and self.tokenizer.symbol() == '.':
            self.writeXML() # .
            self.tokenizer.advance()
            self.writeXML() # subroutineName
            self.tokenizer.advance()
        self.writeXML() # (
        self.tokenizer.advance()
        self.compileExpressionList()
        self.writeXML() # )
        self.tokenizer.advance()
        self.writeXML() # ;
        self.tokenizer.advance()
        self.indentation -= 1
        self.file.write('  ' * self.indentation + '</doStatement>\n')       
    
    def compileReturn(self):
        self.file.write('  ' * self.indentation + '<returnStatement>\n')
        self.indentation += 1
        self.writeXML() # return
        self.tokenizer.advance()
        if self.tokenizer.tokenType != 'SYMBOL' and self.tokenizer.symbol() != ';':
            self.compileExpression()
        self.writeXML() # ;
        self.tokenizer.advance()
        self.indentation -= 1
        self.file.write('  ' * self.indentation + '</returnStatement>\n')        

    def compileExpression(self):
        self.file.write('  ' * self.indentation + '<expression>\n')
        self.indentation += 1
        self.compileTerm()
        while self.tokenizer.tokenType() == 'SYMBOL' and self.tokenizer.symbol() in self.op:
            self.writeXML() # op
            self.tokenizer.advance()
            self.compileTerm()
        
        self.indentation -= 1
        self.file.write('  ' * self.indentation + '</expression>\n')

    def compileTerm(self):
        self.file.write('  ' * self.indentation + '<term>\n')
        self.indentation += 1

        if self.tokenizer.tokenType() == 'SYMBOL':
            if self.tokenizer.symbol() == '(':
                self.writeXML() # (
                self.tokenizer.advance()
                self.compileExpression()
                self.writeXML() # )
                self.tokenizer.advance()
            elif self.tokenizer.symbol() in self.unary:
                self.writeXML() # unary
                self.tokenizer.advance()
                self.compileTerm()
        
        elif self.tokenizer.tokenType() != 'IDENTIFIER':
            self.writeXML() # keyword | stringConst | intConst
            self.tokenizer.advance()
        
        else:
            self.writeXML() # identifier
            self.tokenizer.advance()
            if self.tokenizer.symbol() == '[':
                self.writeXML() # [
                self.tokenizer.advance()
                self.compileExpression()
                self.writeXML() # ]
                self.tokenizer.advance()
            elif self.tokenizer.symbol() == '.':
                self.writeXML() # .
                self.tokenizer.advance()
                self.writeXML() # subroutineName
                self.tokenizer.advance()
            if self.tokenizer.symbol() == '(':
                self.writeXML() # (
                self.tokenizer.advance()
                self.compileExpressionList()
                self.writeXML() # )
                self.tokenizer.advance()
        self.indentation -= 1
        self.file.write('  ' * self.indentation + '</term>\n')

    def compileExpressionList(self):
        self.file.write('  ' * self.indentation + '<expressionList>\n')
        self.indentation += 1
        
        while self.tokenizer.tokenType() != 'SYMBOL' or self.tokenizer.symbol() != ')':
            self.compileExpression()
            if self.tokenizer.symbol() == ',':
                self.writeXML() # ,
                self.tokenizer.advance() 
        self.indentation -= 1
        self.file.write('  ' * self.indentation + '</expressionList>\n')        

    def writeXML(self):
        tag = None
        token = None
        if self.tokenizer.tokenType() == 'KEYWORD':
            tag = 'keyword'
            token = self.tokenizer.keyWord()
        elif self.tokenizer.tokenType()  == 'SYMBOL':
            tag = 'symbol'
            token = self.tokenizer.symbol()
            if token in self.XMLentity:
                token = self.XMLentity[token]
        elif self.tokenizer.tokenType()  == 'IDENTIFIER':
            tag = 'identifier'
            token = self.tokenizer.identifier()
        elif self.tokenizer.tokenType()  == 'INT_CONST':
            tag = 'integerConstant'
            token = str(self.tokenizer.intVal())
        elif self.tokenizer.tokenType()  == 'STRING_CONST':
            tag = 'stringConstant'
            token = self.tokenizer.stringVal()

        self.file.write('  ' * self.indentation + '<'+tag+'> '+token+' </'+tag+'>\n')    

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
        compiler = CompliationEngine(file)
        compiler.compileClass()

if __name__ == "__main__":
    main()