#TODO:
#   Item(morphemes=...) constructor
#   toXIGT
#   union

from hypothesis import given, assume
from hypothesis.strategies import lists, text, characters, dictionaries
from morpho.morpho import *
from morpho.wrappers import SIGMA

validtext = lambda: text(min_size = 1, alphabet=set(SIGMA)-set("=,{}#"))
validlists = lambda: lists(validtext(), min_size=1)
validdicts = lambda: dictionaries(keys=validtext(), values=validtext())
# stop short of combining accents

@given(validtext())
def test_form_constructor_and_encoded(form):
    I = Item(form=form)
    assert I._encoded == "#" + form

@given(validtext())
def test_form_constructor_and_method(form):
    I = Item(form=form)
    assert I.form == form
#
#@given(validlists)
#def test_segmentation_constructor_and_encoded(segmentation):
#    I = Item(segmentation=segmentation)
#    items = [s+"{}" for s in segmentation]
#    assert I._encoded == "#" + ''.join(items)
#
#@given(validlists)
#def test_segmentation_constructor_and_method(segmentation):
#    I = Item(segmentation=segmentation)
#    assert I.segmentation() == segmentation
#

@given(validtext(), validdicts())
def test_form_and_features_constructor_and_method(form, features):
    I = Item(form=form, features=features)
    assert I.form == form
    assert I.features == features

#@given(validlists, validdicts)
#def test_segmentation_and_features_constructor_and_method(segmentation, features):
#    I = Item(segmentation=segmentation, features=features)
#    assert I.segmentation() == segmentation
#    assert I.features() == features
#
#@given(validlists, validlists)
#def test_segmentation_and_gloss_constructor_and_method(segmentation, glosses):
#    assume(len(segmentation) >= len(glosses))
#    I = Item(segmentation=segmentation, glosses=glosses)
#    paddedglosses = glosses + [""] * (len(segmentation)-len(glosses))
##    assert I.segmentation() == segmentation
##    assert I.glosses() == paddedglosses
#    assert I.morphemes() == list(zip(segmentation, paddedglosses))
##
#@given(validlists, validlists, validlists, validlists)
#def test_plus_behavior_with_segmentation_and_glosses(Aseg, Bseg, Agl, Bgl):
#    assume(len(Aseg) >= len(Agl))
#    assume(len(Bseg) >= len(Bgl))
#    padAgl = Agl + [""] * (len(Aseg)-len(Agl))
#    padBgl = Bgl + [""] * (len(Bseg)-len(Bgl))
#
#    A = Item(segmentation=Aseg, glosses=Agl)
#    B = Item(segmentation=Bseg, glosses=Bgl)
#    I = A + B
#    assert I.segmentation() == Aseg + Bseg
#    assert I.glosses() == padAgl + padBgl
#    assert I.morphemes() == list(zip(Aseg, padAgl)) + list(zip(Bseg, padBgl))
#
#
#
#@given(validdicts)
#def test_feature_access(features):
#    I = Item(features=features)
#    for key in features:
#        assert getattr(I, key) == features[key]
