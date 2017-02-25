```text
Condit Interpreter
Copyright (C) 2010 Jack Mudge

Introduction
==============
Condit.py is an interpreter for the esoteric programming language "condit", created by Paul 
Equinox Collins. The original specification can be found at http://equ.in/ox/comp/obfuscated/condit/.
This intepreter aims to be completely compatible with the original specification, and as such, any
deviations should extend the language without breaking it as written. I believe this has been
accomplished with this version.

Please send bug reports to jakykong@theanythingbox.com. The home page for this interpreter is/was
http://www.theanythingbox.com/software/condit.htm, where updates may be found. 

Errata
========
Although I did my best to write this in plain, standard Python so it will run anywhere, I can't test
it on any non-linux machines because I simply don't own any. As such, I'll gladly accept bug reports
anyway, but I can't be sure that I can fix problems for other systems.

Python 3.1 porting in progress -- beware of errors. Use version 0.1 with python 2.6.

How To Use
============
Create your source file in a plain text file, then run condit as such:
./condit.py <source-file> 
If, after <source-file>, you put anything else, the interpreter will print the stack at every point
during parsing. Please send this output along with the source file whenever you send a bug report.

Other than that, there's not much to it. It's a pretty simple language and interpreter. 

Happy Hacking!



LANGUAGE
==========
I describe the language here in the terms I used to implement it. The URL to the original specs is
written above, feel free to compare and contrast it to this specification here.

Overall Syntax
--------------
A program consists of a series of when expressions. A when expression is any expression that fits
the following form:
<when> <expression> <then> <action>

To evaluate a when expression, first <expression> is evaluated. It must be a number after this
evaluation. If it is not equal to 0, then <action> is performed. This is done for all such
expressions in a program, in order, until all of the <expression>s are equal to 0.

Whitespace characters act to separate otherwise combinable tokens. Otherwise, it is entirely 
ignored. Newlines carry no additional meaning in this language, i.e., it is perfectly valid to
write a stream of when expressions with no newlines. It is also valid to insert newlines between any
two tokens. Strings may also contain literal newlines in them -- these are considered part of the
string.

Comments begin with ; and continue until the end of the line.

Expressions
-----------
Expressions may be constants, variables, or compound expressions combining these with operators.

There are two data types in Condit: strings and numbers. They may not, except by chop, by converted
between each other. Numbers represent real numbers (i.e., may have a decimal part if desired), and
strings are processed as per Python's rules of evaluation (i.e., "\n" is a newline, etc.). Strings
may not have a literal "'''" in them anywhere, although "\'\'\'" is just fine and may be used as
a replacement. 

Variables may be any series of letters (not numbers). The type of a variable is determined by the 
case of its first letter. Upper-cased variable names are string variables. Lower-cased variable
names are number variables. All variables are arrays. Use [index]name to get a specific index from
that variable. If [index] is omitted, the default is index 0. Index must be a number.

The available operators for expressions are:
+, -, *, /, =, >, <, ()'s
	These have their canonical meanings. +, =, >, <, and ()'s will work on strings, the others work
	only on numbers. 
and, or
	The number 0 is false, all other numbers are true. Strings are an error. These bind more loosely
	than the other operators.
-
	The unary minus operator.
chop, Chop, rnd, eof, |var|
	Chop(S,i) returns the first i characters of S, and removes them from S (which must be a variable).
	chop(S,i) is the same as chop, except that it attempts to evaluate the string as a number.
	rnd(i) returns a random number between 0 and i, including 0, not including i.
	eof(s) returns whether the file specified by s has reached eof (see 'get' under actions)
	|var| returns the length of the array contained in var, i.e, the maximum index that has been
	assigned.
	
All operators bind left-to-right after binding rules are applied. That is, the order of operations
for *,/,+, and - are *not* adhered to (although parens are always evaluated first.). If you need to
enforce an order of operations, use parentheses.

Actions
-------
Actions form the basis of what may be *done* in condit. The available actions are "get", "set",
and "put". The syntax for get and put are identical:
get #string var
put #string var

#string means a literal # symbol, followed by a string expression which should name a file. This is
optional -- if the entire #string bit is left off, then stdin/stdout are used instead. get retrieves
a value and stores it in variable. This is done one entire line at a time from the input -- the line
is a number precisely under the same circumstances as for constants. No newline is kept at the end
of a string, if that is the value to be stored.

Put sends a value out to its output location, but otherwise follows the same semantics as get.

Finally, set assigns a value to a variable (or array index). Its syntax is
set var=value

Where var may be a plain variable name, or an array index, and value must match in type. = is 
a literal in the expression -- it must be precisely "=". 

Any number of actions may be placed after a when. They will be executed in left-to-right order.



THE ORIGINAL
============
There are some differences between this version of condit and the original. It should be noted that
the original condit is almost completely compatible with this version -- i.e., if it's correct under
that description, this interpreter should be able to run it.

Notable differences between them:
- Newlines are entirely ignored (not required between whens, not errors between other tokens).
- Comments have been incorporated. They start with ;.
```
