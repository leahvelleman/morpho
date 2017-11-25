import six
import re
from itertools import chain, repeat
import pynini

class Item(object):
    def __init__(self, other=None, **kwargs):
        if other:
            if type(other) == type(self):
                self._encoded = other._encoded
                self._fsm = other._fsm
            else:
                self._encode_kwargs(form=other)
                self._fsm = pynini.acceptor(self._encoded, token_type="utf8")
        else:
            self._encode_kwargs(**kwargs)
            self._fsm = pynini.acceptor(self._encoded, token_type="utf8")

    def _encode_kwargs(self, **kwargs):
        form = kwargs.get("form", None)
        segmentation = kwargs.get("segmentation", None)
        glosses = kwargs.get("glosses", None)
        features = kwargs.get("features", None)

        if form and (segmentation or glosses):
            raise ValueError("Too many keyword arguments.")

        if form:
            self._encoded = "#"+form
        elif segmentation:
            self._encode_segs_and_glosses(segmentation, glosses)
        else:
            self._encoded = "#"

        self._encode_features(features)

    def _encode_segs_and_glosses(self, segmentation, glosses):
        glosslist = ["{"+gl+"}" for gl in glosses] if glosses else []
        glosslist = chain(glosslist, repeat("{}"))
        items = chain.from_iterable(zip(segmentation, glosslist))
        self._encoded = "#" + ''.join(items)

    def _encode_features(self, features):
        if features:
            featuresEncoded = ''.join(
                    "[" + key + "=" + features[key] + "]"
                    for key in sorted(features))
            self._encoded = featuresEncoded + self._encoded

    @property
    def sigma(self):
        sigma = set()
        isyms = self._fsm.input_symbols()
        osyms = self._fsm.output_symbols()
        for state in self._fsm.states():
            for arc in self._fsm.arcs(state):
                sigma |= {pynini_decode(isyms.find(arc.ilabel))}
                sigma |= {pynini_decode(osyms.find(arc.olabel))}
        return pynini.string_map(s for s in sigma if "\x00" not in s)

    def morphemes(self):
        asString = self._morphemes()._decode()
        print(asString)
        asIter = iter(re.split("{([^{}]*)}", asString))
        asPairs = list(zip(asIter, asIter))
        return asPairs

    def _morphemes(self):
        morphemeGetter = (pynini.transducer(self.sigma, "").star +
                            pynini.transducer("#", "") +
                            self.sigma.star)
        composed = pynini.compose(self._fsm, morphemeGetter)
        return Item(_fsm = composed.project(True))

    def _decode(self):
        paths = self._fsm.paths(input_token_type="symbol")
        path = next(paths)[0]
        return pynini_decode(path)

    def __getattr__(self, attr):
        features = self.features()
        if attr in features:
            return features[attr]
        else:
            raise AttributeError("Item has no feature " + attr)

    def __add__(self, other):
        cls = type(self)
        segmentation = self.segmentation() + other.segmentation()
        glosses = self.glosses() + other.glosses()
        features = self.features()
        features.update(other.features())
        return cls(segmentation=segmentation, glosses=glosses,
                features=features)

class Class(object):
    def __init__(self, seq):
        self._fsm = pynini.union(*(Item(s)._fsm for s in seq))
        self._fsm.optimize() 

    def __contains__(self, f):
        product = pynini.compose(Item(f)._fsm, self._fsm)
        paths = pynini.shortestpath(self._fsm, nshortest=1).paths()
        return len(list(paths)) == 1









def morpho_decode(inputBytes):
    asString = pynini_decode(inputBytes)
    features, rest = asString.split("#")
    features=features.strip("[]").split("][")
    if features[-1] == "":
        features.pop()
    features = dict((f.split("=")[0], f.split("=")[1]) for f in features)
    restSplit = re.split("{([^{}]*)}", rest)
    segmentation = restSplit[::2]
    if segmentation[-1] == "":
        segmentation.pop()
    glosses = restSplit[1::2]
    return features, segmentation, glosses

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
        return "\\"
    return string


