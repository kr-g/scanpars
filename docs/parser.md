
# scanpars.parser - parser for creating a syntax tree from a given grammar

based on a given grammar a syntax tree is constructed.


# how it works 
 
`scanpars.parser` implements a [`botton-up parser`](https://en.wikipedia.org/wiki/Bottom-up_parsing).

in principle it is a variant of a 
[`LR parser`](https://en.wikipedia.org/wiki/LR_parser)
named also
[`LALR(1) parser`](https://en.wikipedia.org/wiki/LALR_parser).

the produced syntax tree is somehow inspired by 
[`lisp`](https://en.wikipedia.org/wiki/Lisp_(programming_language)),
so the output is a list which elements can contain again list elements (hierarchical list).

each [`production rule`](https://en.wikipedia.org/wiki/Formal_grammar#The_syntax_of_grammars)
produces an element in the output list. 
it is possible to have more than one production rule with the same name defined.
those act then as alternative rule for the production. 
if required to distinguish between different alternatives it's possible to assign an `alias` to 
alternative production rules, where the alias is reflected in the output syntax tree.

currently there is no formal grammar like BNF, or EBNF to specify the used grammar.
instead the grammar is defined by class based rules.

currently the following rules are available:

| name | description |
| --- | --- | 
| Terminal | resolved against a value, or type | 
| Call | calls an other Production | 
| And | sequence | 
| Or | alternative | 
| Optional | the rule inside may be there, or not | 
| Repeat | the rule inside is repeated to match the grammar | 


# limitations

the syntax tree is not optimized.

in case a parser for an infix notation might wants to have also sort of
[`shunting-yard algorithm`](https://en.wikipedia.org/wiki/Shunting-yard_algorithm).

alternatively think into the direction of 
[Nikolaus Wirth's](https://en.wikipedia.org/wiki/Niklaus_Wirth)
proposal - as given here in 
[`EBNF`](https://en.wikipedia.org/wiki/Extended_Backus%E2%80%93Naur_form)

    E = T | E "+" T.      # expression
    T = F | T "*" F.      # term
    F = id | "(" E ")".   # factor

reference: 
- Nikolaus Wirth, downloadable section "Compiler Construction", 
   [external link](https://people.inf.ethz.ch/wirth/), Chapter 5


