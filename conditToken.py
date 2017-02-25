#Token.py -- token-holding class and lexical analyzer.
# 
# Quite a bit of grunt-work happens here. Although this file looks pretty long, it actually doesn't
# have all that much in it.
# There are 5 (groups of) things in this file:
# - The token class represents a basic token. It's critical for the parser to handle these.
# - Aggregate classes group actions/expressions together in some generic way.
# - Action classes represent things that the user may do when conditions are met.
# - Expression classes represent the results of expressions.
# - The lexical analyzer splits a file into tokens and ignores comments.

from sys import stdin, stdout
from random import randrange

#The values for variables
variables = {}

#The currently open files for writing.
openWfiles = {}

#The currently open files for reading.
openRfiles = {}


class token( object ):
	''' Holds a single token, or token-like object. '''
	def __init__(self, val, type):
		''' Some special values for type are interpreted below.
		    If it doesn't precisely match these criteria, then it's
		    left up to client functions to deal with the type. 
		    
		    When type in [string,number], the value must be stored in
		    val. For other types, this may or may not be true.'''
		self.type = type
		self.val = val

		if self.type == "ident": #process identifiers
			if self.val  in ["when", "then", "set", "put", "get", "eof", "rnd", "chop", "Chop"]:
				self.type = self.val
			elif self.val in ["and", "or"]:
				self.type = "oper"
			else:
				self.type = "var"

		if self.type == "punct":
			if self.val in ["=", "<", ">", "+", "-", "*", "/"]:
				self.type = "oper"
			else:
				self.type = self.val
		
	def eval( self, index=0 ):
		''' Evaluate a value, returning a representative string or number token.
		    Valid only for stvar, string, nvar, and number. '''
		global variables
		
		if self.type == "var":
			t = "string" if self.val[0].isupper() else "number"
			if self.val in variables:
				if len( variables[self.val] ) < index:
					return token("", t)
				return token( variables[self.val][index], t)
			else:
				if t == "string":
					return token("",t)
				else:
					return token("0",t)
		elif self.type in ["string","number"]:
			return token(self.val, self.type)
		else:
			raise RuntimeError("Invalid type to eval.")

	def assign( self, value, index):
		''' Assign a value token to a variable.
		    Valid only for stvar, nvar. '''
		global variables
		
		if self.type == "var":
				t = "string" if self.val[0].isupper() else "number"
				if not self.val in variables:
					variables[self.val] = []
				if index == None or index.eval().type != "number":
					raise RuntimeError("Assign index must be a number.")
				else:
					i = eval(index.eval().val)
					while len(variables[self.val]) <= i:
						variables[self.val].append( "0" if t == "number" else "" )
					variables[self.val][i] = value.eval().val
		else:
			raise RuntimeError("Invalid type to assign.")
			
	def __repr__(self):
		return "<" + self.type + ":" + self.val + ">"
			

##############
# AGGREGATES #
###################################################################
# Aggregate classes hold one or more of the classes under ACTIONS #
# and EXPRESSIONS below. Their use case is to reduce multiple     #
# actions or expressions into a single action/expression.         #
# The each have the respective eval() or do() method.             #
###################################################################

class action_list( token ):
	''' A list of actions, which are any token that has a .do() method. '''
	def __init__(self):
		token.__init__(self, "actionlist", "action")
		self.list = []
	def add(self, action):
		if action.val == "actionlist":
			self.list = self.list + action.list
		else:
			self.list.append(action)
	def do(self):
		for i in range( 0, len(self.list) ):
			self.list[i].do()

class action_when( token ):
	''' represents an entire line of code, e.g., a when expr then action set. '''
	def __init__(self, cond, action):
		token.__init__(self, "line", "line")
		self.cond = cond
		self.action = action
		
		if None in [cond, action]:
			raise RuntimeError("None in when.")
		
		
	def do(self):
		c = self.cond.eval()
		if c.type != "number":
			raise SyntaxError("String in condition.")

		#when.do() is an exception to the rule. It returns its condition's success.
		if c.val != "0": #if the condition is true
			self.action.do()
			return 1
		else:
			return 0 

class expression( token ):
	''' An expression. The default just returns the value from token. '''
	def __init__(self, e):
		token.__init__(self, "expression", "expression")
		self.expr = e
	def eval( self ):
		return self.expr.eval()





###########
# ACTIONS #
############################################################
# Actions store something to do in the future.             #
# The actions that have been defined for this language are #
# get, set, and put. Every action class has a do() method, #
# which is called for that action to be done at the right  #
# time.                                                    #
############################################################

class action_get( token ):
	''' Defines the get action. '''
	def __init__(self, var, index=token("0","number"), where=None):
		global openRfiles
		
		token.__init__(self, "get", "action")
		self.var = var
		self.index = index
		self.where = where
	
	def do(self):
		global openRfiles
		
		i = self.index.eval()
		v = self.var
		
		if self.where == None:
			line = raw_input()
		else:
			#Determine the filename
			fileNameToken = self.where.eval()
			if fileNameToken.type != "string":
				raise SyntaxError("Filename must be a string.")
			fname = fileNameToken.val
			
			#Open or get the file reference
			if fname in openRfiles:
				f = openRfiles[fname][0]
			else:
				openRfiles[fname] = [ open(fname, "r"), False ]
				f = openRfiles[fname][0]
			
			#Set EOF status, read in a line, etc.
			openRfiles[fname][1] = False #assume not EOF. Find out in a second.
			line = f.readline()
			if line == "":
				openRfiles[fname][1] = True
				openRfiles[fname][0].close()
				openRfiles[fname][0] = open(fname, "r") #restart from beginning of file.
			elif line[-1] == "\n": #disregard the newline at the end.
				line = line[:-1]
				
		if i.type != "number":
			raise SyntaxError("Index must be a number.")
		
		v.assign( token(line,"string"), i )
		
		
		

class action_set( token ):
	''' Defines the set action. '''
	def __init__(self, var, value, index=token("0","number")):
		token.__init__(self, "set", "action")
		self.var = var
		self.value = value
		self.index = index
		
	def do(self):
		if self.var.type == "var":
			i = self.index.eval()
			self.var.assign( self.value.eval(), i )
		else:
			raise RuntimeError("Can't assign non-variables.")
			

class action_put( token ):
	''' Defines the put action. '''
	def __init__( self, expr, where = None ):
		token.__init__(self, "put", "action")
		self.expr = expr
		self.where = where		

	def do(self):
		s = eval( "'''" + self.expr.eval().val + "'''" ) #handle \n, etc.
		if self.where == None:
			print( s,end="") #write w/o newline to stdout.
		else:
			global openWfiles
			
			w = self.where.eval()
			if w.type != "string":
				raise SyntaxError("Filename must be string.")
				
			if w.val in openWfiles:
				f = openWfiles[w.val]
			else:
				openWfiles[w.val] = open(w.val, "w")
				f = openWfiles[w.val]
			
			f.write( s ) #convert \n, etc.	


###############
# EXPRESSIONS #
####################################################################
# Expressions represent data aggregates. The most basic expression #
# the token itself, which evaluates the variable or value therein. #
# The eval() method is required of these classes. It must return a #
# string or number token, which must contain its value in the val  #
# field. The token class itself is an expression as well.          #
# Due to side effects, it should be noted that no eval() method    #
# should evaluate its inputs more than once.                       #
####################################################################
class expr_plus( token ):
	''' Represents the + operator. '''
	def __init__( self, l, r ):
		token.__init__(self, "+", "expression")
		self.left = l
		self.right = r
		if self.left == None or self.right == None:
			raise RuntimeError("Null plus operand.")

	def eval( self ):
		l = self.left.eval()
		r = self.right.eval()
		
		if l.type == "number":
			if r.type != "number":
				raise SyntaxError("Cannot add strings to numbers.")
			l = eval( l.val )
			r = eval( r.val )
			return token( str(l+r), "number")
		else:
			l = l.val
			r = r.val
			return token( l+r, "string" )
					
class expr_minus( token ):
	''' Represents the - operator. '''
	def __init__( self, l, r ):	
		token.__init__(self, "-", "expression")
		self.left = l
		self.right = r

	def eval( self ):
		if self.left == None:
			self.left = token("0", "number") #support unary operator

		l = self.left.eval()
		r = self.right.eval()
		
		if l.type != "number" or r.type != "number":
			raise SyntaxError("Can't subtract non-numbers.")
		l = eval( l.val )
		r = eval( r.val )

		return token( str(l-r), "number" )
		
		
class expr_times( token ):
	''' Represents the * operator '''
	def __init__( self, l, r ):
		token.__init__(self, "*","expression")
		self.left = l
		self.right = r
	def eval(self):
		if self.left == None or self.right == None:
			raise RuntimeError("Null factors.")
		l = self.left.eval()
		r = self.right.eval()
		if l.type != "number" or r.type != "number":
			raise SyntaxError("Can't multiply non-numbers.")
		l = eval( l.val )
		r = eval( r.val )
		
		return token( str(l*r), "number" )


class expr_divide( token ):
	''' Represents the division operator. '''
	def __init__(self, l, r):
		token.__init__(self, "/","expression")
		self.left = l
		self.right = r
		
	def eval(self):
		if None in [self.left, self.right]:
			raise RuntimeError("Not enough operands.")
		
		l = self.left.eval()
		r = self.right.eval()
		
		if l.type != "number" or r.type != "number":
			raise SyntaxError("Can't divide non-numbers.")
		if r.val == "0":
			raise RuntimeError("Division by zero!")
		l = eval(l.val)
		r = eval(r.val)
		
		return token( str(l/r), "number")


class expr_array( token ):
	''' Represents [n]v syntax. '''
	def __init__(self, var, index=token("0","number")):
		token.__init__(self, "array", "expression")
		if None in [index, var]:
			raise SyntaxError("Invalid array expression.")
		if var.type != "var":
			raise RuntimeError("Null variable.")
		self.var = var
		self.index = index

	def eval(self):
		v = self.var
		i = self.index.eval()
		
		if i.type != "number":
			raise SyntaxError("Index must be a number.")
		i = eval(i.val)
		
		return self.var.eval( i )
		

class expr_rand( token ):
	''' Represents rnd(n) syntax '''
	def __init__(self, val):
		token.__init__(self, "rand", "expression")
		self.v = val
		if val == None:
			raise SyntaxError("Rnd requires a number.")
	
	def eval(self):
		n = self.v.eval()
		if n.type != "number":
			raise SyntaxError("Can't pick a random string.")
		
		r = randrange(0, eval(n.val))
		return token(str(r),"number")


class expr_eof( token ):
	''' Represents eof(str) syntax '''
	def __init__(self, string):
		token.__init__(self, "eof", "expression")
		if string == None:
			raise RuntimeError("Null file in eof call.")
		self.st = string
	
	def eval(self):
		global openRfiles
		s = self.st.eval()
		if s.type != "string":
			raise SyntaxError("EOF must be evaluated with a string.")
			
		if s.val not in openRfiles:
			return token("0","number") #unopened files aren't EOF'd yet.
		else:
			if openRfiles[s.val][1]:
				return token("1","number")
			return token("0","number")
		
		

class expr_equal( token ):
	''' Represents the = operator in expressions. '''
	def __init__(self, l, r):
		token.__init__(self, "equals", "expression")
		if None in [l,r]:
			raise RuntimeError("Can't equate None.")
		self.l = l
		self.r = r
	
	def eval(self):
		l = self.l.eval()
		r = self.r.eval()
		
		if l.type != r.type or l.val != r.val:
			return token("0","number")
		return token("1","number")
			
	
class expr_greater( token ):
	''' Represents the > operator in expressions. '''
	def __init__(self, l, r):
		token.__init__(self, "greater","expression")
		if None in [l,r]:
			raise RuntimeError("Can't compare None.")
		self.l = l
		self.r = r
	
	def eval(self):
		l = self.l.eval()
		r = self.r.eval()
		
		if l.type != r.type:
			raise SyntaxError("Can't compare across types.")
		elif l.val > r.val:
			return token("1","number")
		else:
			return token("0","number")


class expr_less( token ):
	''' Represents the < operator in expressions. '''
	def __init__(self, l, r):
		token.__init__(self, "less","expression")
		if None in [l,r]:
			raise RuntimeError("Can't compare None.")
		self.l = l
		self.r = r
	
	def eval(self):
		l = self.l.eval()
		r = self.r.eval()
		
		if l.type != r.type:
			raise SyntaxError("Can't compare across types.")
		elif l.val < r.val:
			return token("1","number")
		else:
			return token("0","number")


class expr_and( token ):
	''' Represents the and logical operator. '''
	def __init__(self, l, r):
		token.__init__(self, "and","expression")
		if None in [l,r]:
			raise RuntimeError("Can't compare None.")
		self.l = l
		self.r = r
	
	def eval(self):
		l = self.l.eval()
		r = self.r.eval()
		
		if l.type != "number" or r.type != "number":
			raise SyntaxError("Only numbers are boolean.")
		
		
		if "0" in [r.val, l.val]:
			return token("0","number")
		else:
			return token("1","number")

class expr_or( token ):
	''' Represents the or logical operator. '''
	def __init__(self, l, r):
		token.__init__(self, "and","expression")
		if None in [l,r]:
			raise RuntimeError("Can't compare None.")
		self.l = l
		self.r = r
	
	def eval(self):
		l = self.l.eval()
		r = self.r.eval()
		
		if l.type != "number" or r.type != "number":
			raise SyntaxError("Only numbers are boolean.")
		
		if r.val == l.val == "0":
			return token("0","number")
		else:
			return token("1","number")
			
class expr_var( token ):
	''' Converts a token(*,"var") to a token(*,"expression") '''
	def __init__(self, t):
		token.__init__(self, "var", "expression")
		if t.type != "var":
			raise RuntimeError("Non-variable passed to expr_var.")
		self.t = t
	
	def eval(self):
		return self.t.eval()

class expr_chop( token ):
	''' Represents the Chop(var, number) expression '''
	def __init__(self, var, num, index=token("0","number")):
		token.__init__(self, "chop","expression")
		if None in [var, num]:
			raise RuntimeError("None passed to chop.")
		self.var = var
		self.num = num
		self.index = index
	
	def eval(self):
		v = self.var
		n = self.num.eval()
		i = self.index.eval()
		
		if v.type != "var" or n.type != "number":
			raise SyntaxError("Invalid chop expression.")
		p = eval(n.val)
		
		s = v.eval(eval(i.val))
		if s.type != "string":
			raise SyntaxError("cannot chop non-strings.")
		s = s.val
		
		s1 = s[p:]
		s2 = s[:p]
		if p<0: s1,s2 = s2,s1
		
		v.assign( token(s1,"string"), i ) #side-effect
		
		return token(s2, "string")


class expr_chopnum( token ):
	''' Represents the chop(var, number) expression '''
	def __init__(self, var, num, index=token("0","number")):
		token.__init__(self, "chop","expression")
		if None in [var, num]:
			raise RuntimeError("None passed to chop.")
		self.var = var
		self.num = num
		self.index = index
	
	def eval(self):
		v = self.var
		n = self.num.eval()
		i = self.index.eval()
		
		if v.type != "var" or n.type != "number":
			raise SyntaxError("Invalid chop expression.")
		p = eval(n.val)
		
		s = v.eval(eval(i.val))
		if s.type != "string":
			raise SyntaxError("cannot chop non-strings.")
		s = s.val
		
		s1 = s[p:]
		s2 = s[:p]
		if p<0: s1,s2 = s2,s1
		
		#find the number.
		r = ""
		for j in range(0, len(s2)):
			if s2[j].isdigit or s2[j] in [".", "-"]:
				r = r + s2[j]
			else:
				break
		
		v.assign( token(s1,"string"), i ) #side-effect
		
		
		
		return token(r if r != "" else "0", "number")

		

class expr_const( token ):
	''' Converts a token(*,["string","number"]) to a token(*,"expression") '''
	def __init__(self, t):
		token.__init__(self, "const", "expression")
		if t.type not in ["string","number"]:
			raise RuntimeError("Non-variable passed to expr_var.")
		self.t = t
	
	def eval(self):
		return self.t.eval()


####################
# LEXICAL ANALYZER #
#####################################################
# A straightforward lexical analyzer. This language #
# is simple enough that no regular expressions or   #
# fancy coding is really needed.                    #
#####################################################
def lex(line):
	''' Return the stream of tokens representing the source '''
	#Easier lexing if we have a bit of whitespace at the end.
	line = line + "  "

	tokens = []
	tok = ""
	toktype = ""
	while len(line) > 2:
		if line[0].isspace(): #end last token, or ignore
			if toktype != "":
				tokens.append( token(tok, toktype) )
				tok = ""
				toktype = ""
			line = line[1:]
			continue
		elif line[0] == ';': #comment
			if toktype != "":
				tokens.append( token(tok, toktype) )
				tok = ""
				toktype = ""
			line = line[ line.index("\n"): ]
			continue
		elif line[0] == '"': #start a string
			line = line[1:]
			index = line.index('"') #raises exception on no EOS
			tokens.append(token(line[0:index], "string"))
			line = line[index+1:]
		elif line[0].isalpha(): #start an identifier or keyword
			if toktype != "ident" and toktype != "":
				tokens.append( token(tok, toktype) )
				tok = ""
			else:
				toktype = "ident"
				tok = tok + line[0]
				line = line[1:]
		elif line[0].isdigit() or line[0] == ".": #start a number
			if toktype != "number" and toktype != "":
				tokens.append( token(tok, toktype) )
				tok = ""
			else:
				toktype = "number"
				tok = tok + line[0]
				line = line[1:]
		elif line[0] in ['=', '<', '>', ',', '+', '-', '*', '/', '(', ')', '|', '#', '[', ']']: #punctuation
			if toktype != "":
				tokens.append( token(tok, toktype) )
			tokens.append( token(line[0], "punct") )
			toktype = ""
			tok = ""
			line = line[1:]
		else:
			raise SyntaxError("Unexpected character: " + line[0])
	
	
	return tokens



