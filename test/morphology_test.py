import copy
import pynini
from hypothesis import given, assume
from hypothesis.strategies import lists, text, dictionaries, tuples, composite, integers
from morpho.morpho import Form, Morphology, LETTER, makeFstString, suffix

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

@given(forms())
def test_form_morphemes_constructor(f):
    g = Form(lemmaMorphemes=f.lemmaMorphemes,
             morphemes=f.morphemes,
             features=f.features)
    assert g == f

@given(forms())
def test_form_seg_and_gloss_constructor(f):
    g = Form(lemmaSegmentation=f.lemmaSegmentation,
             lemmaGloss=f.lemmaGloss,
             segmentation=f.segmentation,
             gloss=f.gloss,
             features=f.features)
    assert g == f

@given(forms(), forms())
def test_form_inequality(f, g):
    assume(f.lemmaSegmentation != g.lemmaSegmentation or
            f.lemmaGloss != g.lemmaGloss or
            f.segmentation != g.segmentation or
            f.gloss != g.gloss or
            f.features != g.features)
    assert f != g

def test_foo():
    f = Form(segmentation=['a'], gloss=['a'], lemmaSegmentation=['a'], lemmaGloss=['a'], features={})
    g = Form(segmentation=['a'], gloss=['b'], lemmaSegmentation=['a'], lemmaGloss=['a'], features={})
    assert f != g
    f = Form(segmentation=['4'], gloss=['4'], lemmaSegmentation=['4'], lemmaGloss=['4'], features={})
    g = Form(segmentation=['4'], gloss=['4'], lemmaSegmentation=['4'], lemmaGloss=['4'], features={'4': '4'})
    assert f != g

@given(forms())
def test_form_from_strings(f):
    topString = makeFstString(f.lemmaMorphemes, f.features)
    bottomString = makeFstString(f.morphemes, f.features)
    g = Form.fromStrings(top=topString, bottom=bottomString)
    assert g == f

@given(forms())
def test_form_to_and_from_strings_is_noop(f):
    assert Form.fromStrings(*f.toStrings()) == f

@given(forms())
def test_form_to_and_from_fst_is_noop(f):
    assert Form.fromFst(f.toFst()) == f

def test_empty_morphology_creation():
    m = Morphology()
    assert m._fst == pynini.Fst()

@given(forms())
def test_adding_one_form(f):
    m = Morphology()
    m.add_form(f)
    assert Form.fromFst(m._fst) == f


@given(forms(), forms())
def test_addition_order_is_irrelevant(f, g):
    m = Morphology()
    m.add_form(f)
    m.add_form(g)
    n = Morphology()
    n.add_form(g)
    n.add_form(f)
    assert m == n

@given(forms(), forms())
def test_unequal_contents_test_unequal(f, g):
    assume(f != g)
    m = Morphology()
    m.add_form(f)
    n = Morphology()
    n.add_form(g)
    assert m != n

@given(forms(), forms())
def test_query_segmentation(f, g):
    assume(f.segmentation != g.segmentation)
    m = Morphology()
    m.add_form(f)
    m.add_form(g)
    result = m.query(segmentation=f.segmentation) 
    assert f in result
    assert g not in result 

@given(forms(), forms())
def test_query_gloss(f, g):
    assume(f.gloss != g.gloss)
    m = Morphology()
    m.add_form(f)
    m.add_form(g)
    result = m.query(gloss=f.gloss) 
    assert f in result
    assert g not in result


@given(forms(), forms())
def test_query_both(f, g):
    assume(f.segmentation != g.segmentation or f.gloss != g.gloss)
    m = Morphology()
    m.add_form(f)
    m.add_form(g)
    result = m.query(segmentation=f.segmentation, gloss=f.gloss) 
    assert f in result
    assert g not in result

@given(forms(), forms())
def test_query_features(f, g):
    assume(f.features != g.features)
    m = Morphology()
    m.add_form(f)
    m.add_form(g)
    result = m.query(features=f.features)
    assert f in result
    assert g not in result


@given(forms(), forms(), forms())
def test_multi_result_query(f, g, h):
    g.segmentation = f.segmentation
    g.gloss = f.gloss
    m = Morphology()
    m.add_form(f)
    m.add_form(g)
    m.add_form(h)
    result = m.query(segmentation=f.segmentation)
    for x in [f,g,h]:
        if x.segmentation == f.segmentation:
            assert x in result
        else:
            assert x not in result


# TODO:
#   Query for plain text
#   Tests for query on lemma side
#   Tests for multipart query
#   Query with features passed as keyword arguments, not as a dict,
#       or as both.

#   Repository

#   Tests for multi-return-value queries

#   Counterpart to query that returns one thing or fails

#   good __str__ and __repr__ for Morphology objects

#   HARD: can we come up with a good leipzig-friendly sound change 
#       function that will delete hyphens or replace them with colons as
#       required?


@given(forms(), forms())
def test_suffix(f, g):
    m = Morphology()
    m.add_form(f)
    m.add_rule(suffix(g.segmentation, g.gloss))
    print(list(m._fst.paths()))
    result = m.query(segmentation=" ".join(f.segmentation))
    assert len(result) == 1
    #assert result.text == f.text + g.text
