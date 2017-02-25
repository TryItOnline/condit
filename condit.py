#!/usr/bin/python
# Condit.py - a condit interpreter
# See: http://equ.in/ox/comp/obfuscated/condit/
# Ex-Copyright (C) 2010, Jack Mudge
#
# Released as Public Domain by the Author,
# in the sincere (but unfounded) hope that it
# may be useful to someone.
#
# Run as:
# condit.py <source-file>

from sys import argv

from conditToken import lex
from eval import *



def compare( tokens, types ):
	''' Syntactic convenience in the parser.
	    Returns true if types matches on tokens.
	    A sort of mini-regex matching. '''

	if len(tokens) < len(types):
		return False

	for i in range(0, len(types)):
		if tokens[-i-1].type != types[-i-1]:
			return False
	return True


def lookahead( tokens, index ):
	if index+2 >= len(tokens):
		return None
	else:
		return tokens[index+1].type



def parse( tokens ):
	''' Parse tokens as a series of when statements. Return the resultant stack of actions. '''
	index = -1
	stack = []

	get = True #True when another token should be pushed onto the stack.

	while True:
		#entire line - evaluate to a token(*,"line")
		if compare( stack, ['when','expression','then','action'] ):
			stack[-4:] = eval_when( stack[-3], stack[-1], lookahead(tokens, index) )

		if get == True:
			index = index + 1
			if( index < len(tokens) ):
				stack.append( tokens[index] )
		else:
			get = True
			
		if len(argv) > 2:
			print( stack )

		#Constant values need to be expressions to match anything below.
		if compare( stack, ['number']) or compare(stack,['string']):
			stack[-1:] = eval_const( stack[-1] )

		#Check to make sure each line of code is actually complete.
		if compare( stack, ['when'] ):
			if len(stack) >= 2 and stack[-2].type != "line":
				raise SyntaxError("Line of code not completed.")

		#Join actions
		if compare( stack, ['action', 'action'] ):
			stack[-2:] = combine_actions( stack[-2], stack[-1] )
			get = False
			
		#Set action w/ Array
		if compare( stack, ['set', '[', 'expression', ']', 'var']):
			get = True
			continue #lookahead
		if compare( stack, ['set', '[', 'expression', ']', 'var', 'oper', 'expression'] ):
			if lookahead(tokens,index) == 'oper': #expr's not done
				get = True; continue
			else:
				stack[-7:] = eval_setarr( stack[-5], stack[-3], stack[-2], stack[-1] )
				get = False
				
		#Set action w/o Array
		if compare( stack, ['set', 'var'] ):
			get = True
			continue #lookahead
		if compare( stack, ['set','var','oper','expression'] ):
			if lookahead(tokens,index) == 'oper':
				get = True; continue
			else:
				stack[-4:] = eval_set( stack[-3], stack[-2], stack[-1] )
				get = False


		#Put action w/ #
		if compare( stack, ['put', '#', 'expression', 'expression'] ):
			if lookahead(tokens,index) == 'oper':
				get=True; continue
			stack[-4:] = eval_putst( stack[-2], stack[-1] )
			get = False

		#Put action w/o #
		if compare( stack, ['put', 'expression'] ):
			if lookahead(tokens,index) == 'oper':
				get=True; continue
			stack[-2:] = eval_put(stack[-1])
			get = False

		#Get action w/ #
		if compare( stack, ['get', '#', 'expression', 'var'] ):
			stack[-4:] = eval_getst(stack[-2], stack[-1])
			get = False

		#Get action w/o #
		if compare( stack, ['get', 'var']):
			stack[-2:] = eval_get(stack[-1])
			get = False
			
		#Get action w/ array w/ #
		if compare( stack, ['get', '#', 'expression', '[', 'expression', ']', 'var'] ):
			stack[-7:] = eval_getstarr( stack[-5], stack[-1], stack[-3] )
			get = False
		
		#get action w/ array, w/o #
		if compare( stack, ['get', '[', 'expression', ']', 'var'] ):
			stack[-5:] = eval_getarr( stack[-1], stack[-3] )
			get = False


		#Expressions
		#Chop() w/o array
		if compare( stack, ['Chop', '(', 'var']):
			get = True
			continue #lookahead
		if compare( stack, ['Chop', '(', 'var', ',', 'expression', ')']):
			stack[-6:] = eval_chop(stack[-4], stack[-2])
			get = False
		
		#Chop w/ array
		if compare( stack, ['Chop', '(', '[', 'expression', ']', 'var'] ):
			get = True
			continue
		if compare( stack, ['Chop', '(', '[', 'expression', ']', 'var', ',', 'expression', ')']):
			stack[-9:] = eval_choparr(stack[-4], stack[-2], stack[-6])
			get = False
			
		#chop() w/o array
		if compare( stack, ['chop', '(', 'var']):
			get = True
			continue #lookahead
		if compare( stack, ['chop', '(', 'var', ',', 'expression', ')']):
			stack[-6:] = eval_chopnum(stack[-4], stack[-2])
			get = False
		
		#chop w/ array
		if compare( stack, ['chop', '(', '[', 'expression', ']', 'var'] ):
			get = True
			continue
		if compare( stack, ['chop', '(', '[', 'expression', ']', 'var', ',', 'expression', ')']):
			stack[-9:] = eval_chopnumarr(stack[-4], stack[-2], stack[-6])
			get = False
			
			
		#Array
		if compare( stack, ['[', 'expression', ']', 'var']):
			stack[-4:] = eval_array( stack[-3], stack[-1] )
			get = False

		#Rnd(#)
		if compare( stack, ['rnd', '(', 'expression', ')'] ):
			stack[-4:] = eval_rand(stack[-2] )
			get = False

		#Eof(#)
		if compare( stack, ['eof', '(', 'expression', ')'] ):
			stack[-4:] = eval_eof(stack[-2])
			get = False

		# |var|
		if compare( stack, ['|', 'var']):
			get = True
			continue #lookahead
		if compare( stack, ['|', 'var', '|'] ):
			stack[-3:] = eval_pipe(stack[-2])
			get = False

		# Parens
		if compare( stack, ['(', 'expression', ')']):
			stack[-3:] = [ stack[-2] ] #Expression would already be simplified now.
			get = False

		# Operators
		if compare( stack, ['expression', 'oper', 'expression'] ):
			#Deal with binding properly, i.e., "*/+-" bind more closely than "=><" which bind
			#more closely than "and" and "or".
			#This is a violation of the general rule that only the token type should matter here.
			if stack[-2].val in ["and","or"] and lookahead(tokens,index) == "oper":
				get = True; continue
			stack[-3:] = eval_oper( stack[-3], stack[-2], stack[-1] )
			get = False

		# Special case: Unary operator -
		if compare( stack, ['oper', 'expression'] ) and not compare(stack,['expression','oper','expression']):
			if stack[-2].val == "-":
				stack[-2:] = eval_uniop( stack[-2], stack[-1] )
				get = False


		# Variables evaluate to an expression if nothing else matches them.
		if compare( stack, ['var'] ):
			stack[-1:] = eval_var( stack[-1] )
			get = False

			
			
		#Some (not all!) known erroneous expressions
		errors = [] #no easy ones just yet.

		for error in errors:
			if compare( stack, error ):
				raise SyntaxError()

		# Determine if we should end the loop.
		# Must loop until we're out of tokens.
		if index >= len(tokens):
			do = False
			#Keep going until the entire stack is just lines.
			for tok in stack:
				if tok.type != "line":
					do = True
			if do == False: break

	#After parsing, the stack contains lines of code.
	return stack











if __name__ == "__main__":
	# Open source file, as per spec on the command line.
	if len(argv) < 2:
		file = open("test.cdt", "r")
	else:
		file = open(argv[1], "r")


	s = file.read() #Beware of giant source files.
	source = lex( s )	
	actions = parse(source)

	del source, s #Free up just a *bit* of memory.
	
	
	#Run.
	w = 2 #get into the loop the first time.
	while w != 0:
		w = 0
		for a in actions:
			w = w + a.do()
			
