#The various eval_* functions used in the parser
#  -- Note that most of the error handling should be done in token.py, not here.
#  -- The various classes in token.py can verify the data types that they can accept.
#  -- The only errors that should be checked for here are syntactic errors and None parameters.
#
#  -- NOTHING should actually be evaluated here. Some evaluations, such as chop, have side effects.


from conditToken import *

def eval_when( cond, action, lookahead ):
	''' Return an appropriate action_when token.
	    If lookahead is *not* 'when', then do *not* do anything,
	    but instead allow the next action to be collected. '''
	if lookahead != "when" and lookahead != None: #not a complete statement!
		return [ token("when","when"), cond, token("then","then"), action ] #don't change anything!
	
	#setup an appropriate action_when token.
	return [ action_when(cond, action) ]


def combine_actions( action1, action2 ):
	''' Combine two actions into one action-list '''
	if action1.type != "action" or action2.type != "action":
		raise RuntimeError("Not actions.")
	act = action_list()
	act.add( action1 )
	act.add( action2 )
	return [ act ]

def eval_array( index, var ):
	''' Evaluate array expressions. '''
	return [ expr_array(var, index) ]

def eval_setarr( index, var, oper, val ):
	if oper.type != "oper" or oper.val != "=":
		raise SyntaxError("Invalid assignment.")
	return [ action_set( var, val, index ) ]

def eval_set( var, oper, val ):
	''' Assign val to var. '''
	return eval_setarr( token("0","number"), var, oper, val )

def eval_putst( expr, val ):
	''' Put val into the file named by expr. '''
	return [ action_put( val, expr ) ]

def eval_put( val ):
	''' Put val onto stdout '''
	return [ action_put( val ) ]

def eval_getstarr( expr, var, index ):
	''' Get a value from the file named by expr into an array'''
	return [ action_get( var, index, expr ) ]

def eval_getst( expr, var ):
	''' Get a value from the file named by expr '''
	return eval_getstarr( expr, var, token("0","number") )

def eval_get( var ):
	''' Get a value from stdin into var '''
	return [ action_get( var ) ]
	
def eval_getarr( var, index ):
	''' Get a value from stdin into [index]var '''
	return [ action_get( var, index ) ]

def eval_eof( string ):
	''' Evaluate eof(string) '''
	global openRfiles

	if string == None:
		raise RuntimeError("Null filename.")
	return [ expr_eof( string ) ]

def eval_pipe( var ):
	global variables
	
	if var == None or var.type != "var":
		return SyntaxError("Non-variables don't have array lengths.")
	else:
		if var.val in variables:
			return token( str(len(variables[var.val])), "number" )
		else:
			return token("0","number") #non-existant arrays are, obviously, zero-length :)

def eval_oper( exp1, oper, exp2 ):
	''' Evaluate operator expressions '''
	if None in [exp1, oper, exp2]:
		raise RuntimeError("Bad operator call.")
	
	if oper.val == "+":
		return [ expr_plus(exp1, exp2) ]
	elif oper.val == "-":
		return [ expr_minus(exp1, exp2) ]
	elif oper.val == "*":
		return [ expr_times(exp1, exp2) ]
	elif oper.val == "/":
		return [ expr_divide(exp1, exp2) ]
	elif oper.val == "=":
		return [ expr_equal(exp1, exp2) ]
	elif oper.val == ">":
		return [ expr_greater(exp1, exp2) ]
	elif oper.val == "<":
		return [ expr_less(exp1, exp2) ]
	elif oper.val == "and":
		return [ expr_and(exp1, exp2) ]
	elif oper.val == "or":
		return [ expr_or(exp1, exp2) ]
	else:
		raise SyntaxError("Unknown operator.")
		
def eval_uniop( oper, exp ):
	''' Evaluate unary operator expressions.
	    The only supported operator of this type is -. '''
	if None in [oper, exp] or oper.type != "oper":
		raise RuntimeError("Bad operator call.")
	
	if oper.val == "-":
		return [ expr_minus( None, exp ) ]
	else:
		raise SyntaxError("Unsupported unary operator.")
		
def eval_var( var ):
	''' Evaluate a variable to a value. '''
	return [ expr_var( var ) ]

def eval_rand( number ):
	''' Evaluate rnd(number) '''
	if number == None:
		raise RuntimeError("Bad rnd call.")
	
	return [ expr_rand( number ) ]
	
def eval_chop( var, number ):
	''' Evaluate Chop( var, number ) '''
	if None in [var, number]:
		raise SyntaxError("Invalid chop expression.")
	
	return [ expr_chop( var, number ) ]
	
def eval_choparr( var, number, index ):
	''' Evaluate Chop( [index]var, number ) '''
	if None in [var, number, index]:
		raise SyntaxError("Invalid chop expression.")
	return [ expr_chop( var, number, index ) ]
	
def eval_chopnumarr( var, number, index ):
	''' evaluate chop( var, number ) '''
	if None in [var, number, index]:
		raise SyntaxError("Invalid Chop expression.")
	return [ expr_chopnum( var, number, index ) ]
	
def eval_chopnum( var, number ):
	''' evaluate chop( var, number ) '''
	return eval_chopnumarr( var, number, token("0","number") )
	
def eval_const( const ):
	''' Return an equivalent expression for a constant. '''
	#This conditional is an exception to the general rule. Constants are a special case.
	if const == None or const.type not in ['string','number']:
		raise RuntimeError("Invalid constant call.")
	else:
		return [ expr_const( const ) ]
		
	


