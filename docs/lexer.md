
# scanpars.lexer - lexeme analysis scanner tokenizer

`scanpars.lexer` is a 1-to-1 scanner and tokenizer with no-loss of information. 

if required extra whitespace information can be removed from the token stream easily (see sample).

`scanpars.lexer` will create Token or 
[`Lexeme`](https://en.wikipedia.org/wiki/Lexical_analysis#Lexeme)
where each token has a value and annotation depending on the matched lexical rule.

internally a look-ahead is used to produce the right lexeme


# how to create / use lexical analysis rules

lexical analysis is done by well formed rules where the  best one 
(greedy one) is used to produce the exact lexem.

so it doesnt matter in which order rules are placed in the definition.

E.G. the result of performing the rules for '=' and '==' will produce always the right '==' lexem
output when scanning an '==' from the stream since there is a look-ahead performed internally
for finding the greedy solution.

for creating custom lex rules refer also to the predefined set here: 
[`utils.py`](https://github.com/kr-g/scanpars/blob/main/scanpars/lexer/utils.py)


# samples


code: (e.g.)


    def test_float(self):
        inp_text = """
            0. +0. .0 +.0 0.0 +0.1 0.0e-1 +0.0e-1 0.0e1 .0e1 -.0e1
            """
        stream = self.lexx.tokenize(inp_text)
        self.stream = Sanitizer().whitespace(stream)

        res = list(map(lambda x: float(x[0]), self.stream))

        self.assertEqual(
            res,
            [0.0, +0.0, 0.0, +0.0, 0.0, +0.1, 0.0e-1, +0.0e-1, 0.0e1, 0.0e1, -0.0e1],
        )
    

or:

        inp_text = """
            0. +0. .0 +.0 0.0 +0.1 0.0e-1 +0.0e-1 0.0e1 .0e1 -.0e1
            """
        stream = self.lexx.tokenize(inp_text)
        #self.stream = Sanitizer().whitespace(stream)
    
        for tok in self.stream:
            print(tok)


                ('\n', 'LF')
                ('0.', 'FLOAT')
                (' ', 'BLANK')
                ('+0.', 'FLOAT')
                (' ', 'BLANK')
                ('.0', 'FLOAT')
                (' ', 'BLANK')
                ('+.0', 'FLOAT')
                (' ', 'BLANK')
                ('0.0', 'FLOAT')
                (' ', 'BLANK')
                ('+0.1', 'FLOAT')
                (' ', 'BLANK')
                ('0.0e-1', 'FLOAT')
                (' ', 'BLANK')
                ('+0.0e-1', 'FLOAT')
                (' ', 'BLANK')
                ('0.0e1', 'FLOAT')
                (' ', 'BLANK')
                ('.0e1', 'FLOAT')
                (' ', 'BLANK')
                ('-.0e1', 'FLOAT')
                ('\n', 'LF')


or another sample output (without coding):


                ('\n', 'LF')
                ('    ', 'TABED') # 4 BLANK are replaced by 1 Token 'TABED'
                ('    ', 'TABED') # dont like this TABED Token here? 
                ('    ', 'TABED') # dont add it to the lexer, then 4 BLANK are produced
                ('-112', 'INT')
                (' ', 'BLANK')
                ('+110', 'INT')
                (' ', 'BLANK')
                ('110', 'UINT')  # UINT is different from INT !!!
                (' ', 'BLANK')
                ('\n', 'LF')
                ('    ', 'TABED')
                ('    ', 'TABED')
                ('    ', 'TABED')
                ('(-2+1j)', 'COMPLEX_NUM') # new in version v0.0.2
   
   
# limitations

the pre-defined rules in the `utils` module are samples and might not fit all needs for each and everyone, 
or may be even conflicting with them. in case they shall be used as a base for defining proper ones.




    
