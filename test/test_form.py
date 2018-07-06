import copy
from hypothesis import given
from hypothesis.strategies import lists, text, dictionaries, tuples, composite, integers
from morpho.morpho import Form, letter, makeFstString

def to_set(fst):
    """ Convert an acceptor FST to a python set with the same contents. """
    return set(a for a, _, _ in fst.paths())

letters = to_set(letter)

validtext = lambda: text(min_size=1, alphabet=letters)
validlists = lambda: lists(validtext(), min_size=1)
validDicts = lambda: dictionaries(keys=validtext(), values=validtext())

@composite
def glossPairLists(draw):
    limit = draw(integers(min_value=1, max_value=20))
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

@given(glossPairLists(), glossPairLists(), validDicts())
def test_morpheme_constructor(morphemes, lemmaMorphemes, features):
    f = Form(morphemes=morphemes, lemmaMorphemes=lemmaMorphemes,
            features=features)
    assert f.morphemes == morphemes
    assert f.lemmaMorphemes == lemmaMorphemes
    assert f.features == features

@given(glossPairLists(), glossPairLists(), validDicts())
def test_individual_constructor_to_morphemes(morphemes, lemmaMorphemes, features):
    segmentation, gloss = zip(*morphemes)
    lemmaSegmentation, lemmaGloss = zip(*lemmaMorphemes)
    f = Form(segmentation=segmentation,
             gloss=gloss,
             lemmaSegmentation=lemmaSegmentation,
             lemmaGloss=lemmaGloss,
             features=features)
    assert f.morphemes == morphemes
    assert f.lemmaMorphemes == lemmaMorphemes
    assert f.features == features

@given(glossPairLists(), glossPairLists(), validDicts())
def test_constructor_equivalence(morphemes, lemmaMorphemes, features):
    segmentation, gloss = zip(*morphemes)
    lemmaSegmentation, lemmaGloss = zip(*lemmaMorphemes)
    f = Form(segmentation=segmentation,
             gloss=gloss,
             lemmaSegmentation=lemmaSegmentation,
             lemmaGloss=lemmaGloss,
             features=features)
    g = Form(morphemes=morphemes,
             lemmaMorphemes=lemmaMorphemes,
             features=features)
    assert f.morphemes == g.morphemes
    assert f.lemmaMorphemes == g.lemmaMorphemes
    assert f.features == g.features

@given(forms())
def test_equality(f):
    assert f == copy.deepcopy(f)

@given(forms())
def test_eval_repr_is_noop(f):
    assert eval(repr(f)) == f

@given(forms())
def test_to_fst_bottom(f):
    totalString = makeFstString(f.morphemes, f.features)
    assert f.toFst().stringify() == totalString

@given(forms())
def test_to_fst_top(f):
    totalString = makeFstString(f.lemmaMorphemes, f.features)
    assert f.toFst().project().stringify() == totalString

@given(forms())
def test_to_and_from_fst_is_noop(f):
    assert Form.fromFst(f.toFst()) == f
