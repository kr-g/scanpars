from .lexer import (
    Plain,
    NotPlain,
    InSet,
    NotInSet,
    Repeat,
    OR,
    AND,
    OPT,
    Any,
)


class Sanitizer(object):
    def whitespace(self, stream, keep=None):
        whipe = [
            "LF",
            "CR",
            "LFCR",
            "BLANK",
            "TABED",
        ]
        if keep:
            for k in keep:
                whipe.remove(k)
        return filter(
            lambda x: x[1] not in whipe,
            stream,
        )


class RuleBuilder(object):
    def __init__(self, tokens=None):
        if tokens == None:
            tokens = []
        self.org_tokens = tokens
        self.tokens = []

    def __repr__(self):
        return self.__class__.__name__ + "( " + str(self.tokens) + " )"

    def add_all(self):
        all_func = [
            self.add_whitespace,
            self.add_operators_basic,
            self.add_operators_logic,
            self.add_operators_others,
            self.add_commons,
            self.add_tab_replace,
            self.add_char_word,
            self.add_numbers_basic,
            self.add_numbers_float,
            self.add_numbers_complex,
            self.add_identifier,
            self.add_comments,
            self.add_quoted_strings,
            self.add_triple_quoted_strings,
        ]
        [func() for func in all_func]
        return self

    def build(self):
        comb = []
        comb.extend(self.org_tokens)
        comb.extend(self.tokens)
        return comb

    def add_whitespace(self):
        self.tokens.extend(
            [
                (" ", "BLANK"),
                ("\t", "TAB"),
                ("\n", "LF"),
                # a string definition will become a Plain definition internally, such as ...
                (Plain("\r"), "CR"),
                # the next one is more greedy; so it'll take precedence over above.
                # here rule order placement in token list is therefore irrelevant
                ("\n\r", "LFCR"),
                #
            ]
        )
        return self

    def add_operators_basic(self):
        self.tokens.extend(
            [
                ("+", "PLUS"),
                ("-", "MINUS"),
                ("*", "MULT"),
                ("/", "DIV"),
                #
                ("(", "B_OPEN"),
                (")", "B_CLOSE"),
                #
                ("%", "MOD"),
                ("**", "POW"),
                ("^^", "POW_C"),
                # ("//", "FLOOR"),# removed since same as eol comment
                #
            ]
        )
        return self

    def add_operators_logic(self):
        self.tokens.extend(
            [
                ("&&", "LOG_AND"),
                ("||", "LOG_OR"),
                ("!", "LOG_NOT"),
                ("^", "LOG_XOR"),
                #
                ("~", "TILDE"),
                ("&", "AND"),
                ("|", "PIPE"),
                #
                ("<<", "LOG_SHIFT_LEFT"),
                (">>", "LOG_SHIFT_RIGHT"),
                ("<<<", "LOG_USHIFT_LEFT"),
                (">>>", "LOG_USHIFT_RIGHT"),
                #
                ("=", "ASSIGN"),
                (":=", "ASSIGNED"),  # as used in ALGOL
                ("::=", "ASSIGNED_BNF"),  # as used in bnf
                #
                ("<", "LOWER"),
                (">", "GREATER"),
                ("<=", "LEQ"),
                (">=", "GEQ"),
                #
                ("==", "EQUAL"),
                ("===", "IDENTITY"),
                ("!==", "NOIDENTITY"),
                #
            ]
        )

    def add_operators_others(self):
        self.tokens.extend(
            [
                #
                ("++", "INC"),
                ("--", "DEC"),
                #
                ("[", "SB_OPEN"),
                ("]", "SB_CLOSE"),
                ("{", "CB_OPEN"),
                ("}", "CB_CLOSE"),
            ]
        )
        return self

    def add_commons(self):
        self.tokens.extend(
            [
                # 3rd parameter is to indicate that's used just as as part of another terminal
                # eg UNDERSCORE as part of an NAMED (see latter...)
                # otherwise single _ would produce UNDERSCOPE instead of NAMED (wanted)
                ("_", "UNDERSCORE", False),
                (".", "DOT", False),
                (
                    "...",
                    "ELIPSE",
                ),
                ("\\", "ESC", False),
                # the ANY function accepts the next following char from the stream
                (Any(), "ANY", False),
                ("'", "QUOTE", False),
                ('"', "DBLQUOTE", False),
                #
                (",", "COMMA"),
                (":", "COLON"),
                # commonly used as seperator between commands - in most of the languages
                (";", "SEMICOLON"),
            ]
        )

        return self

    def add_tab_replace(self, blank_cnt=4):
        self.tokens.extend(
            [
                (
                    # same as
                    # AND(["BLANK", "BLANK", "BLANK", "BLANK"]),
                    Repeat("BLANK", cnt=blank_cnt),
                    "TABED",
                ),  # 4 blanks in a row produce a single TAB token
            ]
        )
        return self

    def add_char_word(self, blank_cnt=4):
        self.tokens.extend(
            [
                (
                    InSet(
                        [
                            ("a", "z"),  # a range sequence
                            ("A", "Z"),
                        ]
                    ),
                    "CHAR",
                    False,
                ),  # defines a set / range of valid chars
                (Repeat("CHAR"), "WORD"),
            ]
        )
        return self

    def add_numbers_basic(self, blank_cnt=4):
        self.tokens.extend(
            [
                (InSet([("0", "9")]), "DIGIT", False),
                (Repeat("DIGIT"), "UINT"),
                #
                (InSet(["-", "+"]), "SIGNED", False),
                (OPT("SIGNED"), "OPTSIGN", False),  # optional -+ sign
                (AND(["OPTSIGN", "UINT"]), "INT"),  # UINT is different from INT!
                #
                ("0", "ZERO", False),
                (InSet([("0", "9"), ("a", "f"), ("A", "F")]), "HEXDIGIT", False),
                #
                (InSet(["x", "X"]), "_HEXTRAIL", False),
                (AND(["ZERO", "_HEXTRAIL", Repeat("HEXDIGIT")]), "HEXNUM"),
                #
                (InSet(["b", "B"]), "_BINTRAIL", False),
                (InSet(["0", "1"]), "BINDIGIT", False),
                (AND(["ZERO", "_BINTRAIL", Repeat("BINDIGIT")]), "BINNUM"),
                #
                (InSet(["o", "O"]), "_OCTTRAIL", False),
                (InSet([("0", "8")]), "OCTDIGIT", False),
                (AND(["ZERO", "_OCTTRAIL", Repeat("OCTDIGIT")]), "OCTNUM"),
            ]
        )
        return self

    def add_numbers_complex(self, blank_cnt=4):
        self.tokens.extend(
            [
                (
                    AND(
                        [
                            "B_OPEN",
                            OPT("SIGNED"),
                            OR(["FLOAT", "UINT"]),
                            "SIGNED",
                            OR(["FLOAT", "UINT"]),
                            Plain("j"),
                            "B_CLOSE",
                        ]
                    ),
                    "COMPLEX_NUM",
                ),
            ]
        )
        return self

    def add_numbers_float(self, blank_cnt=4):
        self.tokens.extend(
            [
                (
                    AND(
                        [
                            OR(
                                [
                                    AND(["INT", "DOT"]),
                                    AND(["OPTSIGN", "DOT", "DIGIT"]),
                                ]
                            ),
                            OPT("UINT"),
                            OPT(
                                [
                                    InSet(["e", "E"]),
                                    "OPTSIGN",
                                    "UINT",
                                ]
                            ),
                        ]
                    ),
                    "FLOAT",
                ),
            ]
        )
        return self

    def add_identifier(self, blank_cnt=4):
        self.tokens.extend(
            [
                (
                    OR(
                        [
                            "CHAR",
                            "UNDERSCORE",
                            "DIGIT",
                        ]
                    ),
                    "_PART_OF_NAMED",
                    False,  # not use as terminal!
                ),
                (
                    AND(
                        [
                            Repeat("CHAR"),
                            Repeat("_PART_OF_NAMED"),
                        ]
                    ),
                    "IDENTIFIER",
                ),
                (
                    AND(
                        [
                            Repeat("UNDERSCORE"),
                            OPT(Repeat("_PART_OF_NAMED")),
                        ]
                    ),
                    "NAMED",
                ),
            ]
        )
        return self

    def add_comments(self, blank_cnt=4):
        self.tokens.extend(
            [
                (
                    AND(
                        [
                            Plain("/*"),
                            Repeat(NotPlain("*/"), "*"),
                            Plain("*/"),
                        ]
                    ),
                    "BLOCK_COMMENT",
                ),
                (
                    AND(
                        [
                            Plain("(*"),
                            Repeat(NotPlain("*)"), "*"),
                            Plain("*)"),
                        ]
                    ),
                    "BLOCK_ROUND_COMMENT",
                ),
                (
                    AND(
                        [
                            Plain("#"),
                            Repeat(NotInSet(["\n", "\r"]), "*"),
                            # InSet(["\n", "\r"]),
                        ]
                    ),
                    "EOL_COMMENT_PY",
                ),
                (
                    AND(
                        [
                            Plain("//"),
                            Repeat(NotInSet(["\n", "\r"]), "*"),
                            # InSet(["\n", "\r"]),
                        ]
                    ),
                    "EOL_COMMENT",
                ),
            ]
        )
        return self

    def add_quoted_strings(self, blank_cnt=4):
        self.tokens.extend(
            [
                (AND(["ESC", "ANY"]), "ESC_ANY", False),
                (
                    AND(
                        [
                            "QUOTE",
                            Repeat(
                                OR(
                                    [
                                        NotInSet(["'", "\\", "\n", "\r"]),
                                        "ESC_ANY",
                                        # AND(["ESC", "ANY"]),
                                    ]
                                ),
                            ),
                            "QUOTE",
                        ]
                    ),
                    "QUOTED",
                ),
                (
                    AND(
                        [
                            "DBLQUOTE",
                            Repeat(
                                OR(
                                    [
                                        NotInSet(['"', "\\", "\n", "\r"]),
                                        "ESC_ANY",
                                        # AND(["ESC", "ANY"]),
                                    ]
                                ),
                            ),
                            "DBLQUOTE",
                        ]
                    ),
                    "DBLQUOTED",
                ),
            ]
        )

        return self

    def add_triple_quoted_strings(self, blank_cnt=4):
        self.tokens.extend(
            [
                ('"""', "TRIPLE_QUOTE", False),  # a named Plain !
                (
                    AND(
                        [
                            "TRIPLE_QUOTE",
                            Repeat(
                                NotPlain('"""'),
                            ),
                            "TRIPLE_QUOTE",
                        ]
                    ),
                    "TRIPLEQUOTED",
                ),
            ]
        )

        return self
