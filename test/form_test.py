from test.utils import *

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

@given(forms(), forms())
def test_inequality(f, g):
    assume(f.morphemes != g.morphemes or 
           f.lemmaMorphemes != g.lemmaMorphemes or
           f.features != g.features)
    assert f != g

def test_specific_inequalities():
    f = Form(segmentation=['a'], gloss=['a'], lemmaSegmentation=['a'], lemmaGloss=['a'], features={})
    g = Form(segmentation=['a'], gloss=['b'], lemmaSegmentation=['a'], lemmaGloss=['a'], features={})
    assert f != g
    f = Form(segmentation=['4'], gloss=['4'], lemmaSegmentation=['4'], lemmaGloss=['4'], features={})
    g = Form(segmentation=['4'], gloss=['4'], lemmaSegmentation=['4'], lemmaGloss=['4'], features={'4': '4'})
    assert f != g

@given(forms())
def test_eval_repr_is_noop(f):
    assert eval(repr(f)) == f

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
