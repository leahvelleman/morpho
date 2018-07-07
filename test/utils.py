import copy
import pynini
from hypothesis import given, assume
from hypothesis.strategies import lists, text, dictionaries, tuples, composite, integers
from morpho.form import Form, makeFstString
from morpho.morphology import Morphology
from morpho.transducers import LETTER

def to_set(fst):
    """ Convert an acceptor FST to a python set with the same contents. """
    return set(a for a, _, _ in fst.paths())

letters = to_set(LETTER)

validtext = lambda: text(min_size=1, alphabet=letters)
validlists = lambda: lists(validtext(), min_size=1)
validDicts = lambda: dictionaries(keys=validtext(), values=validtext())

@composite
def glossPairLists(draw):
    limit = draw(integers(min_value=1, max_value=8))
    pairs = []
    for _ in range(limit):
        s = draw(text(alphabet=letters, min_size=1))
        g = draw(text(alphabet=letters, min_size=1))
        fixity = draw(integers(min_value=-1, max_value=1))
        if fixity == -1:
            s = s + "-"
            g = g + "-"
        elif fixity == 1:
            s = "-" + s
            g = "-" + g
        pairs.append((s, g))
    return pairs

@composite
def forms(draw):
    return Form(morphemes=draw(glossPairLists()),
                lemmaMorphemes=draw(glossPairLists()),
                features=draw(validDicts()))


