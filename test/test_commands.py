from hypothesis import given
from hypothesis.strategies import lists, text, characters
import morpho

validtext = text(min_size=1, alphabet=characters(max_codepoint=767))
# stop short of combining accents


@given(lists(validtext), lists(validtext))
def test_match(matches, herrings):
    acceptor = morpho.match(*matches)
    for match in matches:
        assert match in acceptor
    for herring in herrings:
        if herring not in matches:
            assert herring not in acceptor

