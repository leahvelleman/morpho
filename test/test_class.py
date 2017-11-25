#TODO:
#   Form(morphemes=...) constructor
#   toXIGT
#   concatenation
#   union

from hypothesis import given, assume
from hypothesis.strategies import lists, text, characters, dictionaries
from morpho.morpho import *

validtext = text(min_size=1, alphabet=characters(max_codepoint=767,
    blacklist_characters=[u"[", u"]", u"\x00", u"{", u"}", u"#", u",", u"=", u" "]))
validlists = lists(validtext, min_size=1)
validdicts = dictionaries(keys=validtext, values=validtext)
# stop short of combining accents


@given(validlists)
def test_class_constructor_and_contains(surfaces):
    C = Class(surfaces)
    for surface in surfaces:
        assert surface in C
