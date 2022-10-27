import time


class NoSolutionFound(Exception):
    pass


class BufferOverflow(Exception):
    pass


class SolvFunc(object):
    def debug(self, dgb=None):
        if "_debug" not in self.__dict__:
            self._debug = None
        if dgb == None:
            return self._debug
        self._debug = dgb
        return self

    def valid(self, it):
        try:
            return self._valid(it)
        except BufferOverflow:
            pass  # ignore this exception here
        except:
            raise

    def _valid(self, it):
        raise NotImplementedError()

    def __call__(self, it):
        return self._valid(it)

    def _call(self, it, e):
        if type(e) == str:
            self.debug() and print(e, "-> ", end="")
            res = it.call_token(e)
            self.debug() and print(e, "<- ", res)
        elif isinstance(e, SolvFunc):
            res = e.valid(it)
            self.debug() and print(e, res, it.get_val())
        else:
            raise Exception("call to unknown function", e)
        return res

    def __repr__(self):
        return self.__class__.__name__


class Plain(SolvFunc):
    def __init__(self, plain_pattern):
        if type(plain_pattern) != str:
            raise Exception("not supported", plain_pattern)
        self._pattern = plain_pattern
        self._len = len(self._pattern)

    def _valid(self, it):
        cur = it.peek(self._len)
        if self._pattern == cur:
            it.inc(self._len)
            return True

    def __repr__(self):
        return super().__repr__() + " '" + self._pattern + "'"


class NotPlain(Plain):
    def _valid(self, it):
        cur = it.peek(self._len)
        if self._pattern != cur:
            it.inc()  # move only 1 position
            return True


class Any(SolvFunc):
    """accepts the next char"""

    def _valid(self, it):
        it.inc()
        return True


class SetFunc(SolvFunc):
    def __init__(self, defs):
        self._el = []
        for d in defs:
            if len(d) == 1:  # not a range tuple
                self.extend(d)
            else:
                self.extend_range(d[0], d[1])

    def extend(self, el):
        self._el.extend(el)
        return self

    def extend_range(self, el_sta, el_sto):
        if el_sta >= el_sto:
            raise Exception("wrong range", el_sta, el_sto)
        self.extend([chr(x) for x in range(ord(el_sta), ord(el_sto) + 1)])
        return self

    def __repr__(self):
        return super().__repr__() + " " + str(self._el)


class InSet(SetFunc):
    def _valid(self, it):
        if it.peek() in self._el:
            it.inc()
            return True


class NotInSet(SetFunc):
    def _valid(self, it):
        if it.peek() not in self._el:
            it.inc()
            return True


class Repeat(SolvFunc):
    def __init__(self, other, cnt="+"):
        if cnt not in ["+", "*"]:
            cnt = int(cnt)
            if cnt <= 0:
                raise Exception("must be a positive number", cnt)
        self.cnt = cnt
        # if type(other) not in [str, SolvFunc]:
        #    raise Exception("repeat type not allowed", other)
        self.other = other

    def _valid(self, it):
        res = True
        cnt = 0
        p = it.pos
        while res:
            lp = it.pos
            res = self._call(it, self.other)
            if res:
                cnt += 1
                if lp == it.pos:
                    raise Exception("endless loop")
                if type(self.cnt) == int and cnt >= self.cnt:
                    break
        found = p < it.pos
        if found == True or self.cnt == "*":
            return True

    def __repr__(self):
        return super().__repr__() + "(" + str(self.other) + ")"


class OtherRelFunc(SolvFunc):
    def __init__(self, other):
        if type(other) != list:
            other = [other]
        self.other = other

    def __repr__(self):
        return super().__repr__() + str(self.other)


class OPT(OtherRelFunc):
    def _valid(self, it):
        for e in self.other:
            res = self._call(it, e)
            if not res:
                return True
        return True


class BoolSolvFunc(OtherRelFunc):
    pass


class OR(BoolSolvFunc):
    def _valid(self, it):
        p = it.pos
        for e in self.other:
            it.pos = p
            res = self._call(it, e)
            if res:
                return res
        it.pos = p


class AND(BoolSolvFunc):
    def _valid(self, it):
        p = it.pos
        for e in self.other:
            res = self._call(it, e)
            if not res:
                it.pos = p
                return res
        res = it()
        if not res:
            it.pos = p
        return res


class Tokens(object):
    def __init__(self):
        self.tokens = []
        self.map = {}

    def extend(self, toklist):
        for tok in toklist:
            tok = list(tok)

            # todo refactor
            tok.extend([True for x in range(0, 3 - len(tok))])

            if type(tok[0]) == str:
                tok[0] = Plain(str(tok[0]))

            if isinstance(tok[0], SolvFunc):
                pass  # tok[0] = self._wrap_solvef(tok[0])

            if type(tok[1]) != str:
                raise Exception("no product token")

            self.tokens.append(tok)
            self._add_map(tok)

        return self

    def _add_map(self, tok):
        if tok[1] in self.map:
            raise Exception("found duplicate rule", tok[1])
        self.map[tok[1]] = tok

    def call_token(self, name, it):
        return self.get_token(name).valid(it)

    def get_token(self, name):
        if name not in self.map:
            raise Exception("unkown term", name)
        tok = self.map[name]
        return tok[0]  # SolveFunc

    def __iter__(self):
        return iter(self.tokens)

    def __repr__(self):
        return str(self.map.values())


class token_it(object):
    def __init__(self, t, tokens):
        self.t = t
        self.tokens = tokens
        self.pos = 0

    def __repr__(self):
        return (
            self.__class__.__name__
            + " pos:"
            + str(self.pos)
            + " text:'"
            + self.t[0 : self.pos + 15]
            + "'"
        )

    def call_token(self, name):
        # indirect call to outer scope objects
        return self.tokens.call_token(name, self)

    def peek(self, _len=1, ignore_eof=False):
        if not ignore_eof and self.pos + _len > len(self.t):
            raise BufferOverflow("EOF")
        return self.t[self.pos : self.pos + _len]

    def inc(self, _len=1):
        if self.pos + 1 > len(self.t):
            raise BufferOverflow("EOF")
        self.pos += _len

    def reset(self):
        self.pos = 0

    def __call__(self):
        return self.captured()

    def captured(self):
        return self.pos > 0

    def get_val(self):
        if self.pos == None:
            return None
        return self.t[: self.pos]


class Lexer(object):
    def __init__(self, tokens, debug=False, debugtime=False):
        self.tokens = tokens
        self.debug = debug
        self.debugtime = debugtime

    def resolve(self, ary, func):
        return self._max_pos(ary, func)

    def _max_pos(self, ary, func):
        greedy = None
        symb = None
        for i in ary:
            v = func(i)
            if greedy == None or v > greedy:
                greedy, symb = v, i
        return greedy, symb

    def tokenize(self, inp_text):
        stream = []
        line = 1

        _sta = time.time()

        while len(inp_text) > 0:
            found = []

            for _tok in self.tokens:

                cmp, tok, _use = _tok
                if not _use:
                    continue

                ## todo refactor to single token_it (reuse)
                it = token_it(inp_text, self.tokens)
                if cmp.valid(it):
                    val = it.get_val()
                    found.append((val, tok))

            if len(found) == 0:
                raise NoSolutionFound(
                    ["line", line, "text", stream]  # it.peek(15, ignore_eof=True)]
                )

            # resolve best
            greedy_pos, symb = self.resolve(found, lambda x: len(x[0]))
            stream.append(symb)
            # prepare next round
            inp_text = inp_text[greedy_pos:]

            captured = symb[0]
            line += len(captured.split("\n")) - 1
            if self.debug:
                print(line, symb)

        _sto = time.time()
        if self.debugtime:
            print("time", _sto - _sta)

        return stream
