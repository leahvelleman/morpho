"""
Automatically construct class members? Or find a way to make sure my stateful
tests are tracking the class as it gets changed, including all operations etc?

To test:
    - Object-returning methods give an object of the right type.
        (__getitem__, keys, values, items, paths)
    - Containers that hash equal have the same properties.
    - Set total ordering is transitive, antireflexive, WHAT ELSE?
    - m[{a,b}] == m[a] | m[b]
    - m[∅] is KeyError
    - {item for item in FsmSet(*args, **kwargs)} == set(*args, **kwargs)
    - {k:v for k,v in FsmDict(*args, **kwargs).items()} == dict(*args, **kwargs)
    - With the exception of subscripting with a set, if S is an FsmSet and s is
      a regular set then S.method(*args, **kwargs) == s.method(*args, **kwargs)
    - Same for D and d
    - a * (b+c) == (a*b) + (a*c)
    - a & (b|c) == (a&b) | (a&c)
"""

import unicodedata
import pytest
import six
from hypothesis import given, assume, reject
from hypothesis.strategies import *
from morpho.wrappers import FSM
from random import shuffle

usabletext = lambda: text(alphabet=characters(
    blacklist_characters=['\0', '\1'],
    blacklist_categories=['Cs']))

transducertext = lambda: lists(tuples(usabletext(), usabletext()))

@composite
def acceptortext(draw):
    n = draw(lists(usabletext()))
    return list(zip(n,n))

@composite
def transducers(draw):
    pairs = draw(transducertext())
    transducer = FSM(pairs)
    return transducer

@composite
def fsts(draw):
    pairs = draw(transducertext())
    return FSM(pairs)


@given(transducertext())
def test_wrapper_from_pairs(items):
    assume(items)
    wrapper = FSM(items)
    assert wrapper

@given(transducertext())
def test_item_order_is_unimportant(items):
    assume(items)
    wrapper1 = FSM(items)
    shuffle(items)
    wrapper2 = FSM(items)
    assert wrapper1 == wrapper2

@given(transducertext())
def test_input_items_are_accepted(items):
    assume(items)
    wrapper = FSM(items)
    for item in items:
        assert wrapper.accepts(item[0], side="top")
        assert wrapper.accepts(item[1], side="bottom")

@given(transducertext(), transducertext())
def test_noninput_items_are_not_accepted(items, redHerrings):
    assume(items)
    tops, bottoms = zip(*items)
    wrapper = FSM(items)
    for rh in redHerrings:
        if rh[0] in tops and rh[1] in bottoms:
            reject()
        if rh[0] not in tops:
            assert not wrapper.accepts(rh[0], side="top")
        if rh[1] not in bottoms:
            assert not wrapper.accepts(rh[1], side="bottom")

@given(transducertext())
def test_pathIterator_sidedness(items):
    keys = [item[0] for item in items]
    values = [item[1] for item in items]
    wrapper = FSM(items)
    assert set(keys) == set(wrapper.pathIterator(side="top"))
    assert set(values) == set(wrapper.pathIterator(side="bottom"))
    assert set(items) == set(wrapper.pathIterator(side=None))

@given(transducertext(), transducertext())
def test_concatenation(items1, items2):
    assume(items1)
    assume(items2)
    wrapper1 = FSM(items1)
    wrapper2 = FSM(items2)
    result = wrapper1.concatenate(wrapper2)
    paths = result.pathIterator(side=None)
    manualResult = []
    for i1 in items1:
        for i2 in items2:
            manualResult += [(i1[0]+i2[0], i1[1]+i2[1])]
    assert set(manualResult) == set(paths)

@given(transducertext())
def test_projection(items):
    assume(items)
    tops, bottoms = zip(*items)
    wrapper = FSM(items)
    topwrapper = wrapper.project(side="top")
    bottomwrapper = wrapper.project(side="bottom")
    for i in tops:
        assert topwrapper.accepts(i)
        if i not in bottoms:
            assert not bottomwrapper.accepts(i)
    for i in bottoms:
        assert bottomwrapper.accepts(i)
        if i not in bottoms:
            assert not bottomwrapper.accepts(i)

@given(transducertext(), integers(min_value=0, max_value=5))
def test_star(items, n):
    assume(items)
    wrapper = FSM(items).star()
    for i in items:
        assert wrapper.accepts(i[0]*n, side="top")
        assert wrapper.accepts(i[1]*n, side="bottom")

@given(lists(usabletext()), lists(usabletext()))
def test_boolean_ops_mirror_set_ops(xs, ys):
    x = FSM(xs)
    y = FSM(ys)
    for op in ['isdisjoint', 'issubset', 'issuperset', '__ge__', '__gt__',
               '__le__', '__lt__', '__eq__', '__ne__']:
        fOp = getattr(FSM, op)
        sOp = getattr(set, op)
        assert fOp(x, y) == sOp(set(xs), set(ys))

@given(lists(usabletext()), lists(usabletext()))
def test_constructive_ops_mirror_set_ops(xs, ys):
    x = FSM(xs)
    y = FSM(ys)
    for op in ['__or__', '__and__', '__xor__', '__sub__']:
        fOp = getattr(FSM, op)
        sOp = getattr(set, op)
        assert fOp(x, y) == FSM(sOp(set(xs), set(ys)))

@given(lists(usabletext()), lists(usabletext()), lists(usabletext()))
def test_constructive_operators_mirror_set_construction(xs, ys, zs):
    x = FSM(xs)
    y = FSM(ys)
    z = FSM(zs)
    for op in ['union', 'intersection', 'difference']:
        fOp = getattr(FSM, op)
        sOp = getattr(set, op)
        assert (fOp(x, y, z) == 
                fOp(x, y, set(zs)) == 
                fOp(x, set(ys), z) ==
                fOp(x, set(ys), set(zs)) ==
                FSM(sOp(set(xs), set(ys), set(zs))))

@given(lists(usabletext()), lists(usabletext()))
def test_concatenation(xs, ys):
    xset = FSM(xs)
    yset = FSM(ys)
    zset = xset + yset
    for x in xs:
        for y in ys:
            assert x + y in zset

@given(dictionaries(usabletext(), lists(usabletext(), min_size=1)))
def test_query_retrieves_all_of_the_input_mappings_values(d):
    pairs = [(k, v) for k in d for v in d[k]]
    a = FSM(pairs)
    for k in d:
        assert set(a.query({k})) == set(d[k])

@given(dictionaries(usabletext(), lists(usabletext(), min_size=1)))
def test_getitem_retrieves_one_of_the_input_mappings_values(d):
    pairs = [(k, v) for k in d for v in d[k]]
    a = FSM(pairs)
    for k in d:
        assert a[k] in d[k]

@given(dictionaries(usabletext(), usabletext()),
        one_of(dictionaries(usabletext(), usabletext()), nothing()))
def test_len_matches_set_length_of_input_mappings_items(d, kwargs):
    a = FSM(d, **kwargs)
    assert len(a) == len(set(d.items()) | set(kwargs.items()))

@given(lists(usabletext()), lists(usabletext()),
        one_of(dictionaries(usabletext(), usabletext()), nothing()))
def test_len_matches_set_length_of_input_iterable(l1, l2, kwargs):
    a = FSM(zip(l1, l2), **kwargs)
    assert len(a) == len(set(zip(l1, l2)) | set(kwargs.items()))

@given(fsts())
def test_repr(d):
    assume(not "..." in repr(d))
    assert eval(repr(d)) == d

@given(fsts())
def test_keys_items_and_values_have_same_length(d):
    assert len(list(d.keys())) == len(list(d.values())) == len(list(d.items()))


def normalize_equal(a, b):
    if isinstance(a, str) and isinstance(b, str):
        return unicodedata.normalize('NFC', a) == unicodedata.normalize('NFC',
                b)
    else:
        return a == b

