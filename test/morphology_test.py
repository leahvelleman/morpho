import pynini
from test.utils import *
from morpho.transducers import suffix

def test_empty_morphology_creation():
    m = Morphology()
    assert m._fst == pynini.Fst()

@given(forms())
def test_adding_one_form(f):
    m = Morphology()
    m.addForm(f)
    assert Form.fromFst(m._fst) == f


@given(forms(), forms())
def test_addition_order_is_irrelevant(f, g):
    m = Morphology()
    m.addForm(f)
    m.addForm(g)
    n = Morphology()
    n.addForm(g)
    n.addForm(f)
    assert m == n

@given(forms(), forms())
def test_unequal_contents_test_unequal(f, g):
    assume(f != g)
    m = Morphology()
    m.addForm(f)
    n = Morphology()
    n.addForm(g)
    assert m != n

@given(forms(), forms())
def test_query_segmentation(f, g):
    assume(f.segmentation != g.segmentation)
    m = Morphology()
    m.addForm(f)
    m.addForm(g)
    result = m.query(segmentation=f.segmentation) 
    assert f in result
    assert g not in result 

@given(forms(), forms())
def test_query_gloss(f, g):
    assume(f.gloss != g.gloss)
    m = Morphology()
    m.addForm(f)
    m.addForm(g)
    result = m.query(gloss=f.gloss) 
    assert f in result
    assert g not in result


@given(forms(), forms())
def test_query_both(f, g):
    assume(f.segmentation != g.segmentation or f.gloss != g.gloss)
    m = Morphology()
    m.addForm(f)
    m.addForm(g)
    result = m.query(segmentation=f.segmentation, gloss=f.gloss) 
    assert f in result
    assert g not in result

@given(forms(), forms())
def test_query_features(f, g):
    assume(f.features != g.features)
    m = Morphology()
    m.addForm(f)
    m.addForm(g)
    result = m.query(features=f.features)
    assert f in result
    assert g not in result


@given(forms(), forms(), forms())
def test_multi_result_query(f, g, h):
    g.segmentation = f.segmentation
    g.gloss = f.gloss
    m = Morphology()
    m.addForm(f)
    m.addForm(g)
    m.addForm(h)
    result = m.query(segmentation=f.segmentation)
    for x in [f,g,h]:
        if x.segmentation == f.segmentation:
            assert x in result
        else:
            assert x not in result

@given(forms(), forms(), forms())
def test_iter_method(f, g, h):
    assume(f != h and g != h)
    m = Morphology()
    m.addForm(f)
    m.addForm(g)
    result = list(iter(m))
    assert f in result
    assert g in result
    assert h not in result


# TODO:
#   Query for plain text
#   Tests for query on lemma side
#   Tests for multipart query
#   Query with features passed as keyword arguments, not as a dict,
#       or as both.

#   Counterpart to query that returns one thing or fails

#   Counterpart to query that creates a submorphology

#   Test for Morphology __str__ and __repr__? Is that important?

#   How can Morphology.__iter__() and Morphology.__repr__() handle cyclical
#   fsts? Work on this after addRule so we have a way of making cyclical
#   morphologies.

#   HARD: can we come up with a good leipzig-friendly sound change 
#       function that will delete hyphens or replace them with colons as
#       required?



@given(forms(), forms())
def test_suffix(f, g):
    m = Morphology()
    m.addForm(f)
    m.addRule(suffix(segmentation=g.segmentation, gloss=g.gloss))
    result = m.query(lemmaSegmantation = f.lemmaSegmentation)
    assert len(result) == 1
    assert result[0].text == f.text + g.text
