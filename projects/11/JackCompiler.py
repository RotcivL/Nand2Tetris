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
            while i < len(string) and string[i].isdecimal():
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
    
class SymbolTable:
    def __init__(self):
        self.static = self.field = self.arg = self.var = 0
        self.table = {}

    def reset(self):
        self.static = self.field = self.arg = self.var = 0
        self.table.clear()

    def define(self, name, type, kind):
        index = 0
        if kind == 'static':
            index = self.static
            self.static += 1
        elif kind == 'field':
            index = self.field
            self.field += 1
        elif kind == 'arg':
            index = self.arg
            self.arg += 1
        elif kind == 'var':
            index = self.var
            self.var += 1
        self.table[name] = (kind, type, index)
        
    def varCount(self, kind):
        if kind == 'static':
            return self.static
        elif kind == 'field':
            return self.field
        elif kind == 'arg':
            return self.arg
        elif kind == 'var':
            return self.var

    def kindOf(self, name):
        if name in self.table:
            return self.table[name][0]
        return 'NONE'

    def typeOf(self, name):
        return self.table[name][1]

    def indexOf(self, name):
        return self.table[name][2]
    
class VMWriter:
    def __init__(self, output_file):
        self.kind_to_segment = {'static':'static',
                           'field':'this',
                           'arg':'argument',
                           'var':'local',
                           'pointer':'pointer',
                           'constant':'constant',
                           'temp':'temp',
                           'that':'that'}

        self.file = open(output_file[:-5]+'.vm', 'w')
    
    def writePush(self, segment, index):
        segment = self.kind_to_segment[segment]
        self.file.write('push {} {}\n'.format(segment, index))

    def writePop(self, segment, index):
        segment = self.kind_to_segment[segment]
        self.file.write('pop {} {}\n'.format(segment, index))

    def writeArithmetic(self, command):
        self.file.write(command + '\n') 

    def writeLabel(self, label):
        self.file.write('label {}\n'.format(label))

    def writeGoto(self, label):
        self.file.write('goto {}\n'.format(label))

    def writeIf(self, label):
        self.file.write('if-goto {}\n'.format(label))

    def writeCall(self, name, nArgs):
        self.file.write('call {} {}\n'.format(name, nArgs))

    def writeFunction(self, name, nVars):
        self.file.write('function {} {}\n'.format(name, nVars))

    def writeReturn(self):
        self.file.write('return\n')

    def close(self):
        self.file.close()

class CompliationEngine:
    """
    Outputs vm code from input jack code
    CompilationEngine as recommended in Nand2Tetris chapter 10
    """
    def __init__(self, file):
        """
        Instantiates the tokenizer to get a stream of jack tokens.
        @param file(str): path to .jack file that is being converted to tokens
        """
        self.tokenizer = JackTokenizer(file) 
        self.classVarDec = ['static', 'field']
        self.subroutineDec = ['constructor', 'function', 'method']
        self.op = ['+', '-', '*', '/', '&', '|', '<', '>', '=']
        self.unary = ['~', '-']
        self.classTable = SymbolTable()
        self.subroutineTable = SymbolTable()
        self.writer = VMWriter(file)
        self.className = None
        self.subroutineName = None
        self.counter = 0

    def compileClass(self):
        """
        Compiles a complete class
        """
        self.tokenizer.advance() # class
        self.tokenizer.advance() # className
        self.className = self.tokenizer.identifier()
        self.tokenizer.advance() # {
        self.tokenizer.advance() # classVarDeC | subroutineDec
        self.compileClassVarDec() 
        # subroutineDec
        self.compileSubroutine()
        # }
        self.writer.close()

    def compileClassVarDec(self):
        """
        compiles class variable declarationa
        runs recursively until all class variable declarations have been compiled
        """
        if self.tokenizer.keyWord() not in self.classVarDec:
            return
        # static | field
        kind = self.tokenizer.keyWord()
        self.tokenizer.advance() # type
        self._varDec(kind)
        self.tokenizer.advance() # classVarDec | subroutineDec
        self.compileClassVarDec()

    def compileSubroutine(self):
        """
        compiles a complete method, function or constructor 
        runs recursively until all subroutines have been compiled
        """
        if self.tokenizer.keyWord() not in self.subroutineDec:
            return
        # subtourinteDec
        self.subroutineTable.reset()
        self.counter = 0
        subroutineType = self.tokenizer.keyWord() 
        if subroutineType == 'method':
            self.subroutineTable.define('this', self.className, 'arg')
        
        self.tokenizer.advance() # ('void' | type)
        self.tokenizer.advance() # subroutineName
        self.subroutineName = self.tokenizer.identifier()
        self.tokenizer.advance() # (
        self.tokenizer.advance() # parameter list
        self.compileParameterList() 
        # )
        self.tokenizer.advance() # {
        self.compileSubroutineBody(subroutineType)
        # } subroutine
        self.tokenizer.advance() # } class | subroutineDec
        self.compileSubroutine() 

    def compileParameterList(self):
        """
        compiles a (possibly empty) parameter list
        does not handle enclosing ( and )
        """
        while self.tokenizer.tokenType() != 'SYMBOL':
            # type
            type = self.tokenizer.identifier()
            self.tokenizer.advance() # varName
            name = self.tokenizer.identifier()
            self.subroutineTable.define(name, type, 'arg')
            self.tokenizer.advance() # , | )
            if self.tokenizer.symbol() == ',':
                self.tokenizer.advance() # type 

    def compileSubroutineBody(self, subroutineType):
        """
        compiles a subroutine's body
        """
        self.tokenizer.advance() # var | statement keyword
        self.compileVarDec() 
        # statement keyword
        nVars = self.subroutineTable.varCount('var')
        self.writer.writeFunction(self.className+'.'+self.subroutineName, nVars)
        if subroutineType == 'method':
            self.writer.writePush('arg', 0)
            self.writer.writePop('pointer', 0)
        if subroutineType == 'constructor':
            nFields = self.classTable.varCount('field')
            self.writer.writePush('constant', nFields)
            self.writer.writeCall('Memory.alloc', 1)
            self.writer.writePop('pointer', 0)
        self.compileStatements()


    def compileVarDec(self):
        """
        compiles variable declarations 
        runs recursively until all variable declarations in subroutine have been compiled
        """
        if self.tokenizer.tokenType() != 'KEYWORD' or self.tokenizer.keyWord() != 'var':
            return
        # var
        kind = self.tokenizer.keyWord()
        self.tokenizer.advance() # type
        self._varDec(kind, True)
        self.tokenizer.advance() # var | statement keyword
        self.compileVarDec()        

    def compileStatements(self):
        """
        compiles a sequence of statments
        does not handle enclosing { and }
        """
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
        # }

    def compilelet(self):
        """
        compiles a let statement
        """
        # let
        self.tokenizer.advance() # varName
        varName = self.tokenizer.identifier()
        kind =  self.subroutineTable.kindOf(varName)
        if kind == 'NONE':
            kind = self.classTable.kindOf(varName)
            index = self.classTable.indexOf(varName)
        else:
            index = self.subroutineTable.indexOf(varName)
        self.tokenizer.advance() # [ | =

        if self.tokenizer.symbol() == '[':
            self.writer.writePush(kind, index)
            # [
            self.tokenizer.advance() # exp
            self.compileExpression()
            # ]
            self.writer.writeArithmetic('add')
            self.tokenizer.advance() # =
            self.tokenizer.advance() # exp
            self.compileExpression()
            # ;
            self.writer.writePop('temp', 0)
            self.writer.writePop('pointer', 1)
            self.writer.writePush('temp', 0)
            self.writer.writePop('that', 0)
        else:
            # =
            self.tokenizer.advance() # exp 
            self.compileExpression()
            # ;
            self.writer.writePop(kind, index)
        
        self.tokenizer.advance() # statement keyword | }

    def compileIf(self):
        """
        compiles a if statement with a possible trailing else clause
        """
        # if
        self.tokenizer.advance() # (
        self.tokenizer.advance() # exp
        self.compileExpression()
        # )
        self.writer.writeArithmetic('not')
        label = self.subroutineName + str(self.counter)
        self.counter += 1
        self.writer.writeIf(label)
        self.tokenizer.advance() # {
        self.tokenizer.advance() # statements* if branch
        self.compileStatements()
        # }
        self.tokenizer.advance() # else | statements*
        if self.tokenizer.tokenType() == 'KEYWORD' and self.tokenizer.keyWord() == 'else':
            # else
            label2 = self.subroutineName + str(self.counter)
            self.counter += 1
            self.writer.writeGoto(label2)
            self.writer.writeLabel(label)
            label = label2
            self.tokenizer.advance() # {
            self.tokenizer.advance() # statements* else branch
            self.compileStatements()
            # }
            self.tokenizer.advance() # statements*
        self.writer.writeLabel(label)

    def compileWhile(self):
        """
        compiles a while statement
        """
        # while
        self.tokenizer.advance() # (
        label = self.subroutineName + str (self.counter)
        self.counter += 1
        self.writer.writeLabel(label)
        self.tokenizer.advance() # exp
        self.compileExpression()
        # )
        self.writer.writeArithmetic('not')
        label2 = self.subroutineName + str(self.counter)
        self.counter += 1
        self.writer.writeIf(label2)
        self.tokenizer.advance() # {
        self.tokenizer.advance() # while scope statements
        self.compileStatements()
        # }
        self.writer.writeGoto(label)
        self.writer.writeLabel(label2)
        self.tokenizer.advance() # statements*


    def compileDo(self):
        """
        compiles a do statement
        """
        # do
        self.tokenizer.advance() # subroutineName | (className | varName)
        self.compileExpression() 
        # ; 
        self.writer.writePop('temp', 0)
        self.tokenizer.advance() # statements*
    
    def compileReturn(self):
        """
        compiles a return statmement
        """
        # return
        self.tokenizer.advance() # ; | this | expS
        if self.tokenizer.tokenType == 'SYMBOL' and self.tokenizer.symbol() == ';':
            self.writer.writePush('constant', 0)
        elif self.tokenizer.tokenType == 'KEYWORD' and self.tokenizer.keyWord() == 'this':
            self.writer.writePush('pointer', 0)
        else:
            self.compileExpression()
        # ;
        self.writer.writeReturn()
        self.tokenizer.advance() # }

    def compileExpression(self):
        """
        compiles an expression
        """
        # term
        self.compileTerm() 
        # (op term) | ; | )
        while self.tokenizer.tokenType() == 'SYMBOL' and self.tokenizer.symbol() in self.op:
            # op
            op = self.tokenizer.symbol()
            self.tokenizer.advance() # term
            self.compileTerm()
            # (op term) | ; | )
            self._writeOp(op)


    def compileTerm(self):
        """
        compiles a term
        If current token is an identifer, a single lookahead token [ ( .  is required 
        to distinguish possibilites.
        """

        if self.tokenizer.tokenType() == 'SYMBOL':
            if self.tokenizer.symbol() == '(':
                # (
                self.tokenizer.advance()
                self.compileExpression()
                # )
                self.tokenizer.advance() # (op term) | ;
            elif self.tokenizer.symbol() in self.unary:
                # unary
                unary = self.tokenizer.symbol()
                self.tokenizer.advance() # term
                self.compileTerm()
                # (op term) | ; | )
                self._writeUnary(unary)
        
        elif self.tokenizer.tokenType() != 'IDENTIFIER':
            # keywordConst | stringConst | intConst
            if self.tokenizer.tokenType() == 'KEYWORD':
                self._writeKeywordConst()
            elif self.tokenizer.tokenType() == 'STRING_CONST':
                self._writeString()
            elif self.tokenizer.tokenType() == 'INT_CONST':
                intConst = self.tokenizer.intVal()
                self.writer.writePush('constant', intConst)
            self.tokenizer.advance() # (op term) | ; | )
        
        else:
            # identifier
            identifier = self.tokenizer.identifier()
            kind, index, type = self._searchTable(identifier)

            self.tokenizer.advance() # (op term) | ; | [ | . | ( 
            if self.tokenizer.symbol() == '[':
                # [ array
                # search in subroutine then class
                self.writer.writePush(kind, index)
                self.tokenizer.advance() # exp
                self.compileExpression()
                # ]
                self.writer.writeArithmetic('add')
                self.writer.writePop('pointer', 1)
                self.writer.writePush('that', 0)
                self.tokenizer.advance() # (op term) | ;
                
            elif self.tokenizer.symbol() == '.':
                # . subroutinecall
                # search subroutine then class then it is static function
                # 
                
                if kind == 'NONE':
                    args = 0
                else:
                    self.writer.writePush(kind, index)
                    args = 1
                
                self.tokenizer.advance() # subroutineName
                subroutineName = self.tokenizer.identifier()
                self.tokenizer.advance() # (
                self.tokenizer.advance() # expList
                args += self.compileExpressionList()
                # )
                self.writer.writeCall(type+'.'+subroutineName, args)
                self.tokenizer.advance() # (op term) | ;

            elif self.tokenizer.symbol() == '(':
                # ( subroutine call this.
                subroutineName = identifier
                kind, index, type = self._searchTable('this')
                if kind == 'NONE':
                    self.writer.writePush('pointer', 0)
                    type = self.className
                else:
                    # index = self.subroutineTable.indexOf('this')
                    # type = self.subroutineTable.typeOf('this')
                    self.writer.writePush(kind, index)

                # (
                self.tokenizer.advance()
                args = self.compileExpressionList() + 1
                # )
                self.writer.writeCall(type+'.'+subroutineName, args)
                self.tokenizer.advance() # (op term) | ;
            
            else:
                self.writer.writePush(kind, index)
                # kind = self.subroutineTable.kindOf(identifier)
                # if kind == 'NONE':
                #     kind = self.classTable.kindOf(identifier)
                #     if kind != 'NONE':
                #         index = self.classTable.indexOf(identifier)
                #         self.writer.writePush(kind, index)
                # else:
                #     index = self.subroutineTable.indexOf(identifier)
                #     self.writer.writePush(kind, index)



    def compileExpressionList(self):
        """
        compiles a (possibly empty) list of expressions.
        """
        args = 0
        while self.tokenizer.tokenType() != 'SYMBOL' or self.tokenizer.symbol() != ')':
            args += 1
            self.compileExpression()
            if self.tokenizer.symbol() == ',':
                # ,
                self.tokenizer.advance() # ) | exp
        return args


    def _varDec(self, kind, subroutine=False):
        """
        helper function for use in both varaible declaration functions
        """
        if subroutine:
            table = self.subroutineTable
        else:
            table = self.classTable
        # type 
        type = self.tokenizer.identifier() 
        self.tokenizer.advance() #varName
        name = self.tokenizer.identifier()
        table.define(name, type, kind)
        self.tokenizer.advance() # , | ;        
        while self.tokenizer.symbol() == ',':
            self.tokenizer.advance()
            name = self.tokenizer.identifier() # varName
            table.define(name, type, kind)
            self.tokenizer.advance() # , | ;

    def _writeOp(self, op):
        if op == '+':
            self.writer.writeArithmetic('add')
        elif op == '-':
            self.writer.writeArithmetic('sub')
        elif op == '*':
            self.writer.writeCall('Math.multiply', 2)
        elif op == '/':
            self.writer.writeCall('Math.divide', 2)
        elif op == '&':
            self.writer.writeArithmetic('and')
        elif op == '|':
            self.writer.writeArithmetic('or')
        elif op == '<':
            self.writer.writeArithmetic('lt')
        elif op == '>':
            self.writer.writeArithmetic('gt')
        elif op == '=':
            self.writer.writeArithmetic('eq')
    
    def _writeUnary(self, unary):
        if unary == '-':
            self.writer.writeArithmetic('neg')
        elif unary == '~':
            self.writer.writeArithmetic('not')

    def _writeKeywordConst(self):
        keyword = self.tokenizer.keyWord()
        if keyword == 'true':
            self.writer.writePush('constant', 1)
            self.writer.writeArithmetic('neg')
        elif keyword == 'false' or keyword == 'null':
            self.writer.writePush('constant', 0)
        elif keyword == 'this':
            self.writer.writePush('pointer', 0)
        
    def _writeString(self):
        s = self.tokenizer.stringVal()
        self.writer.writePush('constant', len(s))
        self.writer.writeCall('String.new', 1)
        for c in s:
            self.writer.writePush('constant', ord(c))
            self.writer.writeCall('String.appendChar', 2)

    def _searchTable(self, identifier):
        kind = self.subroutineTable.kindOf(identifier)
        if kind == 'NONE':
            kind = self.classTable.kindOf(identifier)
            if kind == 'NONE':
                return 'NONE', 'NONE', identifier
            index = self.classTable.indexOf(identifier)
            type = self.classTable.typeOf(identifier)
        else:
            index = self.subroutineTable.indexOf(identifier)
            type = self.subroutineTable.typeOf(identifier)

        return kind, index, type

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