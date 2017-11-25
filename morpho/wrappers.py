#pylint: disable=bad-whitespace

# TODO: top/bottom rather than key/value terminology

from itertools import chain
import collections
import six
import operator
import pynini
import pywrapfst

SIGMA = list("qwertyuiopasdfghjkl;'zxcvbnm,./`1234567890-=QWERTYUIOP{}|ASDFGHJKL:\"ZXCVBNM<>?~!@#$%^&*()_+ ")

def _constructiveOp(op):
    def innerFunction(self, *others):
        cls = type(self)
        accum = self.fsm
        for other in others:
            accum = op(accum, cls(other).fsm)
        return cls(accum)
    return innerFunction

class PyniniWrapper(object):
    def __init__(self, arg, **kwargs):
        if isinstance(arg, pynini.Fst):
            self.fsm = arg
        elif isinstance(arg, type(self)):
            self.fsm = arg.fsm
        else:
            if isinstance(arg, collections.Mapping):
                pairs = arg.items()
            else:
                pairs = [a if isinstance(a, tuple) and len(a) == 2 
                           else (a,a) 
                           for a in arg]
            cls = type(self)
            pairs = chain(pairs, kwargs.items())
            self.fsm = pynini.string_map(
                    cls.encodePairs(pairs),
                    input_token_type="utf8",
                    output_token_type="utf8")

    @classmethod
    def encodePairs(cls, pairs):
        for k, v in pairs:
            if "\x00" in k or "\x00" in v:
                raise ValueError
            yield (k, v)

    @classmethod
    def fromFilename(cls, filename):
        fsm = pynini.Fst.read(filename)
        return cls(fsm)

    @classmethod
    def transducer(cls, fsm1, fsm2):
        if not isinstance(fsm1, cls):
            fsm1 = PyniniWrapper.fromItem(fsm1)
        if not isinstance(fsm2, PyniniWrapper):
            fsm2 = PyniniWrapper.fromItem(fsm2)
        fsm = pynini.transducer(fsm1.fsm, fsm2.fsm)
        return cls(fsm)

    def __eq__(self, other):
        em = pynini.EncodeMapper("standard", True, True)
        return pynini.equivalent(pynini.encode(self.fsm, em).optimize(), 
                                 pynini.encode(other.fsm, em).optimize())

    def __repr__(self):
        contents = sorted(list(self.pathIterator(side="both", limit=5)))
        coda = " ... " if len(contents) > 4 else ""
        contents = ", ".join(map(repr, contents[:4])) + coda
        cls = type(self)
        return cls.__name__ + "([" + contents + "])"

    def __getitem__(self, key):
        return next(iter(self.query({key})))

    def __contains__(self, element):
        return self.accepts(element, side="top")

    def __iter__(self):
        return self.pathIterator(side="top")

    def __len__(self):
        return len(list(self.pathIterator()))

    def __invert__(self):
        cls = type(self)
        return cls(SIGMA).star() - self

    def __add__(self, other):
        return self.concatenate(other)

    def __sub__(self, other):
        return self.difference(other)

    def __mul__(self, other):
        return self.cross(other)

    def __matmul__(self, other):
        return self.compose(other)

    def __le__(self, other):
        return self.issubset(other)

    def __lt__(self, other):
        return self.issubset(other) and not self == other

    def __ge__(self, other):
        return self.issuperset(other)

    def __gt__(self, other):
        return self.issuperset(other) and not self == other

    def __and__(self, other):
        return self.intersection(other)

    def __or__(self, other):
        return self.union(other)

    def __xor__(self, other):
        return (self - other) | (other - self)

    def __rshift__(self, other):
        return self.priorityUnion(other)

    def __rlshift__(self, other):
        return self.priorityUnion(other)

    def __lshift__(self, other):
        cls = type(self)
        other = cls(other)
        return other.priorityUnion(self)

    def __rrshift__(self, other):
        cls = type(self)
        other = cls(other)
        return other.priorityUnion(self)

    def lenCompare(self, n, op=operator.eq):
        if n == float('inf'):
            return self.isCyclic()
        if isinstance(n, collections.Iterable):
            return self.numPathsCompare(len(n), op)
        return self.numPathsCompare(n, op)

    def isCyclic(self):
        try: 
            stringpaths = self.fsm.paths()
        except pywrapfst.FstArgError:
            return True
        return False

    def numPathsCompare(self, n, op=operator.eq):
        numToTryFor = n+1
        numFound = len(list(self.pathIterator(limit=numToTryFor)))
        return op(numFound, n)

    def hasPaths(self):
        return self.numPathsCompare(0, operator.gt)

    def accepts(self, item, side="top"):
        cls = type(self)
        wrappedItem = cls([(item, item)])
        if side == "top":
            product = wrappedItem.compose(self)
        else:
            product = self.compose(wrappedItem)
        return product.hasPaths()

    def pathIterator(self, limit=None, side=None):
        if limit is None:
            try:
                stringpaths = self.fsm.paths(
                    input_token_type='symbol',
                    output_token_type='symbol')
            except pywrapfst.FstArgError:
                print("Can't iterate over this mapping. It is cyclic and may accept infinitely many keys.")
                raise
        else:
            stringpaths = pynini.shortestpath(self.fsm, nshortest=limit).paths(
                input_token_type='symbol',
                output_token_type='symbol')
        if side=="top":
            for stringpath in stringpaths:
                yield pynini_decode(stringpath[0])
        elif side=="bottom":
            for stringpath in stringpaths:
                yield pynini_decode(stringpath[1])
        else:
            for stringpath in stringpaths:
                yield (pynini_decode(stringpath[0]),
                       pynini_decode(stringpath[1]))

    def intersection(self, *others):
        self.fsm.optimize()
        return _constructiveOp(pynini.intersect)(self, *others)

    def union(self, *others):
        obj = _constructiveOp(pynini.union)(self, *others)
        obj.fsm.optimize() # Counting paths is inaccurate after union unless
                           # we do this. TODO: more robust solution.
        return obj

    concatenate = _constructiveOp(pynini.concat)
    difference = _constructiveOp(pynini.difference)
    compose = _constructiveOp(pynini.compose)
    lenientlyCompose = _constructiveOp(pynini.leniently_compose)

    def priorityUnion(self, *others):
        cls = type(self)
        accum = self.copy()
        for other in others:
            accum = accum | (~accum.keyset() @ cls(other))
        return accum

    def isdisjoint(self, other):
        return not (self & other).hasPaths()

    def issubset(self, other):
        return not (self - other).hasPaths()

    def issuperset(self, other):
        return not (other - self).hasPaths()

    def project(self, side="top"):
        if side not in {"top", "bottom"}:
            raise ValueError
        tf = (side == "bottom")
        cls = type(self)
        return cls(self.fsm.copy().project(project_output=tf))

    def cross(self, other):
        cls = type(self)
        return cls(pynini.transducer(self.fsm, other.fsm))

    def star(self):
        cls = type(self)
        return cls(pynini.closure(self.fsm).optimize())

    def plus(self):
        cls = type(self)
        return cls(pynini.closure(self.fsm, 1).optimize()) #TEST THIS

    def sigma(self):
        sigma = set()
        isyms = self.fsm.input_symbols()
        osyms = self.fsm.output_symbols()
        for state in self.fsm.states():
            for arc in self.fsm.arcs(state):
                sigma |= {pynini_decode(isyms.find(arc.ilabel))}
                sigma |= {pynini_decode(osyms.find(arc.olabel))}
        cls = type(self)
        return cls((s,s) for s in sigma if "\x00" not in s)

    def makeRewrite(self, 
                    leftEnvironment=None, rightEnvironment=None,
                    leftBottomTape=False, rightBottomTape=False,
                    sigma=None):
        cls = type(self)
        left = leftEnvironment or cls("")
        right = rightEnvironment or cls("")
        sigma = sigma or (self.sigma()
                          .union(left.sigma())
                          .union(right.sigma())
                          .star())
        fsm = pynini.cdrewrite(self.fsm, left.fsm, right.fsm, sigma.fsm)
        return cls(fsm)

    def query(self, querySet):
        return (PyniniWrapper(querySet) @ self).valueset()

    def keys(self):
        return self.pathIterator(side="top")

    def keyset(self):
        """
        Return the keys in the current instance as an :class:`fsa` rather than
        an iterator.
        """
        return PyniniWrapper(self.project(side="top"))

    def values(self):
        return self.pathIterator(side="bottom")

    def valueset(self):
        """
        Return the values in the current instance as an :class:`fsa` rather than
        an iterator.
        """
        return PyniniWrapper(self.project(side="bottom"))

    def items(self):
        return self.pathIterator(side="both")

    def findAmbiguity(self, strictness=100):
        """ Allauzen and Mohri: an FST f is functional (i.e. one-to-one or
        many-to-one) iff f' .o. f is the identity function over f's domain.
        Rather than implement A&Z's algorithm to determine strict identity,
        we test identity for a random sample of paths.
        """
        fpcf = self.fsm.copy().invert() * self.fsm
        for top, bottom, _ in pynini.randgen(fpcf,
                                             npath=strictness,
                                             max_length=strictness)\
                                    .paths(input_token_type="symbol",
                                           output_token_type="symbol"):
            if top != bottom:
                return (clean(top), clean(bottom))
        return None


def pynini_decode(inputBytes):
    """ Pynini often outputs bytestrings with unprintable characters
    represented in an unusual way. Run them through this to get plain unicode.
    """
    asString = inputBytes.decode("utf8")
    asTokens = (from_att_symbol(symbol) for symbol in asString.split(' '))
    return "".join(asTokens)

def from_att_symbol(string):
    """ OpenFST outputs symbol table representations in an awkward
    format. Attempt to deal with that gracefully. """
    # pylint: disable=too-many-return-statements
    if string.startswith("<0"):
        return six.unichr(int(string.strip('<>'), 16))
    if string.startswith("<") and string.endswith(">"):
        return {
            "NUL": chr(0),  "":    chr(0),  "epsilon": chr(0),
            "SOH": chr(1),  "STX": chr(2),  "ETX": chr(3),  "EOT": chr(4),
            "ENQ": chr(5),  "ACK": chr(6),  "BEL": chr(7),  "BS":  chr(8),
            "HT":  chr(9),  "LF":  chr(10), "VT":  chr(11), "FF":  chr(12),
            "CR":  chr(13), "SO":  chr(14), "SI":  chr(15), "DLE": chr(16),
            "DC1": chr(17), "DC2": chr(18), "DC3": chr(19), "DC4": chr(20),
            "NAK": chr(21), "SYN": chr(22), "ETB": chr(23), "CAN": chr(24),
            "EM":  chr(25), "SUB": chr(26), "ESC": chr(27), "FS":  chr(28),
            "GS":  chr(29), "RS":  chr(30), "US":  chr(31), "SPACE": chr(32),
            "DEL": chr(127)
        }[string.strip('<>')]
    if len(string) > 1:
        return "[" + string + "]"
    if string == "[":
        return "\\["
    if string == "]":
        return "\\]"
    if string == "\\":
        return "\\\\"
    return string


