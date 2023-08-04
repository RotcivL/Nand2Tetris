import os
import sys

class JackTokens:
    """
    Class to represent tokens in Jack 
    """
    def __init__(self, type, token):
        self.type = type
        self.token = token
    
class JackTokenizer:
    """
    Converts jack code into a stream of individual jack tokens
    JackTokenizer as recommended in Nand2Tetris chapter 10
    """
    def __init__(self, file):
        """
        Opens jack file for reading, tokenizing jack code
        @param file(str): path to .jack file that is being converted to tokens
        """
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
        """
        parses line to not split strings in quotations
        splits line by whitespace to get preliminary set of tokens (some will need to be further split)
        """
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
        """
        parse preliminary set of tokens, assigning them to jack tokens (with type)
        """
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
        """
        checks to see if tokenizer has reached last token
        """
        return self.current_pos < len(self.tokens) - 1

    def advance(self):
        """
        move current token to next token
        """
        self.current_pos += 1
        self.current_token = self.tokens[self.current_pos]

    def tokenType(self):
        """
        returns the jack type of token
        """
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
    """
    Outputs a structured representation of input jack code in XML.
    CompilationEngine as recommended in Nand2Tetris chapter 10
    """
    def __init__(self, file):
        """
        Instantiates the tokenizer to get a stream of jack tokens.
        @param file(str): path to .jack file that is being converted to tokens
        """
        self.tokenizer = JackTokenizer(file) 
        self.indentation = 0
        self.classVarDec = ['static', 'field']
        self.subroutineDec = ['constructor', 'function', 'method']
        self.op = ['+', '-', '*', '/', '&', '|', '<', '>', '=']
        self.unary = ['~', '-']
        self.XMLentity = {'<':'&lt;', '>':'&gt;', '&':'&amp;', '"':'&quot;'}
        self.file = open(file[:-5] + "Compile2.xml", "w")
        
    def compileClass(self):
        """
        Compiles a complete class
        """
        self.file.write('<class>\n')
        self.indentation += 1
        self.tokenizer.advance() 
        self._writeXML() # class
        self.tokenizer.advance() 
        self._writeXML() # className
        self.tokenizer.advance() 
        self._writeXML() # {
        self.tokenizer.advance()
        self.compileClassVarDec()
        self.compileSubroutine()
        self._writeXML() # }
        self.indentation -= 1
        self.file.write('</class>\n')
        self.file.close()

    def compileClassVarDec(self):
        """
        compiles class variable declarationa
        runs recursively until all class variable declarations have been compiled
        """
        if self.tokenizer.keyWord() not in self.classVarDec:
            return
        self.file.write('  ' * self.indentation + '<classVarDec>\n')
        self.indentation += 1
        self._writeXML() # static | field 
        self.tokenizer.advance() 
        self._varDec()
        self.tokenizer.advance()
        self.indentation -= 1
        self.file.write('  ' * self.indentation + '</classVarDec>\n')
        self.compileClassVarDec()

    def compileSubroutine(self):
        """
        compiles a complete method, function or constructor 
        runs recursively until all subroutines have been compiled
        """
        if self.tokenizer.keyWord() not in self.subroutineDec:
            return
        self.file.write('  ' * self.indentation + '<subroutineDec>\n')
        self.indentation += 1
        self._writeXML() # constructor | function | method
        self.tokenizer.advance()
        self._writeXML() # ('void' | type)
        self.tokenizer.advance()
        self._writeXML() # subroutineName
        self.tokenizer.advance()
        self._writeXML() # (
        self.tokenizer.advance()
        self.compileParameterList() # tokenizer advances until )
        self._writeXML() # )
        self.tokenizer.advance()
        self.compileSubroutineBody()
        self.tokenizer.advance()
        self.indentation -= 1
        self.file.write('  ' * self.indentation + '</subroutineDec>\n')
        self.compileSubroutine()

    def compileParameterList(self):
        """
        compiles a (possibly empty) parameter list
        does not handle enclosing ( and )
        """
        self.file.write('  ' * self.indentation + '<parameterList>\n')
        self.indentation += 1
        while self.tokenizer.tokenType() != 'SYMBOL':
            self._writeXML() # type
            self.tokenizer.advance()
            self._writeXML() # varName
            self.tokenizer.advance()
            if self.tokenizer.symbol() == ',':
                self._writeXML() # ,
                self.tokenizer.advance() 
        self.indentation -= 1
        self.file.write('  ' * self.indentation + '</parameterList>\n')

    def compileSubroutineBody(self):
        """
        compiles a subroutine's body
        """
        self.file.write('  ' * self.indentation + '<subroutineBody>\n')
        self.indentation += 1
        self._writeXML() # {
        self.tokenizer.advance()
        self.compileVarDec()
        self.compileStatements()
        self._writeXML() # }
        self.indentation -= 1
        self.file.write('  ' * self.indentation + '</subroutineBody>\n')

    def compileVarDec(self):
        """
        compiles variable declarations 
        runs recursively until all variable declarations in subroutine have been compiled
        """
        if self.tokenizer.tokenType() != 'KEYWORD' or self.tokenizer.keyWord() != 'var':
            return
        self.file.write('  ' * self.indentation + '<varDec>\n')
        self.indentation += 1
        self._writeXML() # var
        self.tokenizer.advance() 
        self._varDec()
        self.tokenizer.advance()
        self.indentation -= 1
        self.file.write('  ' * self.indentation + '</varDec>\n')
        self.compileVarDec()        

    def compileStatements(self):
        """
        compiles a sequence of statments
        does not handle enclosing { and }
        """
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
        """
        compiles a let statement
        """
        self.file.write('  ' * self.indentation + '<letStatement>\n')
        self.indentation += 1
        self._writeXML() # let
        self.tokenizer.advance()
        self._writeXML() # varName
        self.tokenizer.advance()
        if self.tokenizer.symbol() == '[':
            self._writeXML() # [
            self.tokenizer.advance()
            self.compileExpression()
            self._writeXML() # ]
            self.tokenizer.advance()
        self._writeXML() # =
        self.tokenizer.advance()
        self.compileExpression()
        self._writeXML() # ;
        self.tokenizer.advance()
        self.indentation -= 1
        self.file.write('  ' * self.indentation + '</letStatement>\n')


    def compileIf(self):
        """
        compiles a if statement with a possible trailing else clause
        """
        self.file.write('  ' * self.indentation + '<ifStatement>\n')
        self.indentation += 1
        self._writeXML() # if
        self.tokenizer.advance()
        self._writeXML() # (
        self.tokenizer.advance()
        self.compileExpression()
        self._writeXML() # )
        self.tokenizer.advance()
        self._writeXML() # {
        self.tokenizer.advance()
        self.compileStatements()
        self._writeXML() # }
        self.tokenizer.advance()
        if self.tokenizer.tokenType() == 'KEYWORD' and self.tokenizer.keyWord() == 'else':
            self._writeXML() # else
            self.tokenizer.advance()
            self._writeXML() # {
            self.tokenizer.advance()
            self.compileStatements()
            self._writeXML() # }
            self.tokenizer.advance()
        self.indentation -= 1
        self.file.write('  ' * self.indentation + '</ifStatement>\n')

    def compileWhile(self):
        """
        compiles a while statement
        """
        self.file.write('  ' * self.indentation + '<whileStatement>\n')
        self.indentation += 1
        self._writeXML() # while
        self.tokenizer.advance()
        self._writeXML() # (
        self.tokenizer.advance()
        self.compileExpression()
        self._writeXML() # )
        self.tokenizer.advance()
        self._writeXML() # {
        self.tokenizer.advance()
        self.compileStatements()
        self._writeXML() # }
        self.tokenizer.advance()
        self.indentation -= 1
        self.file.write('  ' * self.indentation + '</whileStatement>\n')        

    def compileDo(self):
        """
        compiles a do statement
        """
        self.file.write('  ' * self.indentation + '<doStatement>\n')
        self.indentation += 1
        self._writeXML() # do
        self.tokenizer.advance()
        # subroutinecall
        self._writeXML() # subroutineName | (className | varName)
        self.tokenizer.advance()
        if self.tokenizer.tokenType() == 'SYMBOL' and self.tokenizer.symbol() == '.':
            self._writeXML() # .
            self.tokenizer.advance()
            self._writeXML() # subroutineName
            self.tokenizer.advance()
        self._writeXML() # (
        self.tokenizer.advance()
        self.compileExpressionList()
        self._writeXML() # )
        self.tokenizer.advance()
        self._writeXML() # ;
        self.tokenizer.advance()
        self.indentation -= 1
        self.file.write('  ' * self.indentation + '</doStatement>\n')       
    
    def compileReturn(self):
        """
        compiles a return statmement
        """
        self.file.write('  ' * self.indentation + '<returnStatement>\n')
        self.indentation += 1
        self._writeXML() # return
        self.tokenizer.advance()
        if self.tokenizer.tokenType != 'SYMBOL' and self.tokenizer.symbol() != ';':
            self.compileExpression()
        self._writeXML() # ;
        self.tokenizer.advance()
        self.indentation -= 1
        self.file.write('  ' * self.indentation + '</returnStatement>\n')        

    def compileExpression(self):
        """
        compiles an expression
        """
        self.file.write('  ' * self.indentation + '<expression>\n')
        self.indentation += 1
        self.compileTerm()
        while self.tokenizer.tokenType() == 'SYMBOL' and self.tokenizer.symbol() in self.op:
            self._writeXML() # op
            self.tokenizer.advance()
            self.compileTerm()
        self.indentation -= 1
        self.file.write('  ' * self.indentation + '</expression>\n')

    def compileTerm(self):
        """
        compiles a term
        If current token is an identifer, a single lookahead token [ ( .  is required 
        to distinguish possibilites.
        """
        self.file.write('  ' * self.indentation + '<term>\n')
        self.indentation += 1

        if self.tokenizer.tokenType() == 'SYMBOL':
            if self.tokenizer.symbol() == '(':
                self._writeXML() # (
                self.tokenizer.advance()
                self.compileExpression()
                self._writeXML() # )
                self.tokenizer.advance()
            elif self.tokenizer.symbol() in self.unary:
                self._writeXML() # unary
                self.tokenizer.advance()
                self.compileTerm()
        
        elif self.tokenizer.tokenType() != 'IDENTIFIER':
            self._writeXML() # keyword | stringConst | intConst
            self.tokenizer.advance()
        
        else:
            self._writeXML() # identifier
            self.tokenizer.advance()
            if self.tokenizer.symbol() == '[':
                self._writeXML() # [
                self.tokenizer.advance()
                self.compileExpression()
                self._writeXML() # ]
                self.tokenizer.advance()
            elif self.tokenizer.symbol() == '.':
                self._writeXML() # .
                self.tokenizer.advance()
                self._writeXML() # subroutineName
                self.tokenizer.advance()
            if self.tokenizer.symbol() == '(':
                self._writeXML() # (
                self.tokenizer.advance()
                self.compileExpressionList()
                self._writeXML() # )
                self.tokenizer.advance()
        self.indentation -= 1
        self.file.write('  ' * self.indentation + '</term>\n')

    def compileExpressionList(self):
        """
        compiles a (possibly empty) list of expressions.
        """
        self.file.write('  ' * self.indentation + '<expressionList>\n')
        self.indentation += 1
        
        while self.tokenizer.tokenType() != 'SYMBOL' or self.tokenizer.symbol() != ')':
            self.compileExpression()
            if self.tokenizer.symbol() == ',':
                self._writeXML() # ,
                self.tokenizer.advance() 
        self.indentation -= 1
        self.file.write('  ' * self.indentation + '</expressionList>\n')        

    def _varDec(self):
        """
        helper function for use in both varaible declaration functions
        """
        self._writeXML() # type
        self.tokenizer.advance() 
        self._writeXML() # varName
        self.tokenizer.advance()
        while self.tokenizer.symbol() == ',':
            self._writeXML() # ,
            self.tokenizer.advance() 
            self._writeXML() # varName
            self.tokenizer.advance()
        self._writeXML() # ;

    def _writeXML(self):
        """
        writes the XML representation of the current token
        """
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
    """
    Syntax analyzer for Jack code
    main program to set up other modules
    """
    files = []
    path = sys.argv[1]
    # check if it is a file
    if os.path.isfile(path):
        ext = path[-5:]
        assert ext == ".jack", "incorrect file type, input must be named like xxx.jack"
        files = [path]
    # check if it is a directory
    elif os.path.isdir(path):
        for file in os.listdir(path):
            # store all .jack files to be parsed
            if file[-5:] == ".jack":
                files.append(os.path.join(path, file))

    for file in files:
        compiler = CompliationEngine(file)
        compiler.compileClass()

if __name__ == "__main__":
    main()