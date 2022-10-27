import unittest

from scanpars.lexer.lexer import (
    Tokens,
    token_it,
    Lexer,
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

from scanpars.lexer.utils import RuleBuilder, Sanitizer


class Any_Path_TestCase(unittest.TestCase):
    def setUp(self):

        tokens = RuleBuilder().add_all().build()
        alltokens = Tokens().extend(tokens)
        self.lexx = Lexer(alltokens, debug=not True, debugtime=True)
        self.stream = None

    def tearDown(self):
        if self.stream:
            # stream = Sanitizer().whitespace(self.stream)
            for tok in self.stream:
                print(tok)

    def test_int_unit(self):
        inp_text = """
            -112 +110 110 
            """
        stream = self.lexx.tokenize(inp_text)
        self.stream = Sanitizer().whitespace(stream)

        res = list(map(lambda x: int(x[0]), self.stream))

        self.assertEqual(res, [-112, +110, 110])

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

    def test_words(self):
        inp_text = """
            a quick brown fox jumps far away
            """
        stream = self.lexx.tokenize(inp_text)
        self.stream = Sanitizer().whitespace(stream)

        res = list(map(lambda x: str(x[0]), self.stream))

        self.assertEqual(
            res,
            "a quick brown fox jumps far away".split(),
        )

    def test_blank_tab(self):
        inp_text = """
            a tabbed        test
            """
        stream = self.lexx.tokenize(inp_text)
        # self.stream = Sanitizer().whitespace(stream)

        res = [
            ("\n", "LF"),
            ("    ", "TABED"),
            ("    ", "TABED"),
            ("    ", "TABED"),
            ("a", "WORD"),
            (" ", "BLANK"),
            ("tabbed", "WORD"),
            ("    ", "TABED"),
            ("    ", "TABED"),
            ("test", "WORD"),
            ("\n", "LF"),
            ("    ", "TABED"),
            ("    ", "TABED"),
            ("    ", "TABED"),
        ]

        self.assertEqual(res, stream)

    def test_quoted_text(self):
        inp_text = """
                'single'
                'single\\nmultiline'
                'single\\'escaped'
                "double"
                "double\\multiline"
                "double\\"escaped"
            """
        stream = self.lexx.tokenize(inp_text)
        self.stream = Sanitizer().whitespace(stream)
        self.stream = list(self.stream)

        res = [
            ("'single'", "QUOTED"),
            ("'single\\nmultiline'", "QUOTED"),
            ("'single\\'escaped'", "QUOTED"),
            ('"double"', "DBLQUOTED"),
            ('"double\\multiline"', "DBLQUOTED"),
            ('"double\\"escaped"', "DBLQUOTED"),
        ]

        self.assertEqual(res, self.stream)

    def test_empty_comments(self):
        inp_text = """
                /**/
                (**)
                # python comment
            """
        stream = self.lexx.tokenize(inp_text)
        self.stream = Sanitizer().whitespace(stream)
        self.stream = list(self.stream)

        res = [
            ("/**/", "BLOCK_COMMENT"),
            ("(**)", "BLOCK_ROUND_COMMENT"),
            ("# python comment", "EOL_COMMENT_PY"),
        ]

        self.assertEqual(res, self.stream)

    def test_multiline_comments(self):
        inp_text = """
                /*
                test
                // test
                
                */
                (*
                test
                // test
                
                *)
            """
        stream = self.lexx.tokenize(inp_text)
        self.stream = Sanitizer().whitespace(stream)
        self.stream = list(self.stream)

        res = [
            (
                "/*\n                test\n                // test\n                \n                */",
                "BLOCK_COMMENT",
            ),
            (
                "(*\n                test\n                // test\n                \n                *)",
                "BLOCK_ROUND_COMMENT",
            ),
        ]

        self.assertEqual(res, self.stream)

    def test_multiline_triple_quoted(self):
        inp_text = """
\"\"\"
    pythonic triple
    qouted multiline
    comment
    text with 'single' \t and "double" text inside
\"\"\"
        """
        stream = self.lexx.tokenize(inp_text)
        self.stream = Sanitizer().whitespace(stream)
        self.stream = list(self.stream)

        res = [
            (
                '"""\n    pythonic triple\n    qouted multiline\n    comment\n    text with \'single\' \t and "double" text inside\n"""',
                "TRIPLEQUOTED",
            )
        ]

        self.assertEqual(res, self.stream)

    def test_other_base_numbers(self):
        inp_text = """
            0x1234
            0b1011
            0o678
            0X1234
            0B1011
            0O678
            """
        stream = self.lexx.tokenize(inp_text)
        self.stream = Sanitizer().whitespace(stream)
        self.stream = list(self.stream)

        res = [
            ("0x1234", "HEXNUM"),
            ("0b1011", "BINNUM"),
            ("0o678", "OCTNUM"),
            ("0X1234", "HEXNUM"),
            ("0B1011", "BINNUM"),
            ("0O678", "OCTNUM"),
        ]

        self.assertEqual(res, self.stream)

    def test_complex(self):
        cmplx = -2 + 1j
        inp_text = str(cmplx)

        stream = self.lexx.tokenize(inp_text)
        self.stream = Sanitizer().whitespace(stream)
        self.stream = list(self.stream)

        res = [("(-2+1j)", "COMPLEX_NUM")]

        self.assertEqual(res, self.stream)
        self.assertEqual(complex(res[0][0]), cmplx)

        print("found", cmplx)

    def test_complex_multi(self):

        inp_text = """
            (2-1j)(-2-1j)
            (.2-1j) (-.2-1j)
            (2.-1j) (-2.-1j)
            (2.0-1j) (-2.0-1j)
            (2-.1j) (2-1.j)
            (2-0.1j) (2-1.0j)
        """

        stream = self.lexx.tokenize(inp_text)
        self.stream = Sanitizer().whitespace(stream)
        self.stream = list(self.stream)

        res = [
            ("(2-1j)", "COMPLEX_NUM"),
            ("(-2-1j)", "COMPLEX_NUM"),
            ("(.2-1j)", "COMPLEX_NUM"),
            ("(-.2-1j)", "COMPLEX_NUM"),
            ("(2.-1j)", "COMPLEX_NUM"),
            ("(-2.-1j)", "COMPLEX_NUM"),
            ("(2.0-1j)", "COMPLEX_NUM"),
            ("(-2.0-1j)", "COMPLEX_NUM"),
            ("(2-.1j)", "COMPLEX_NUM"),
            ("(2-1.j)", "COMPLEX_NUM"),
            ("(2-0.1j)", "COMPLEX_NUM"),
            ("(2-1.0j)", "COMPLEX_NUM"),
        ]

        self.assertEqual(res, self.stream)
