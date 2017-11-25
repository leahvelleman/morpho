import six
import re
from itertools import chain, repeat
import pynini
from .wrappers import FSM, SIGMA


class Item(object):
    def __init__(self, other=None, **kwargs):
        if other:
            if type(other) == type(self):
                self._encoded = other._encoded
                self._fsm = other._fsm
            else:
                self._encode_kwargs(form=other)
                self._fsm = FSM(self._encoded)
        else:
            self._encode_kwargs(**kwargs)
            self._fsm = FSM(self._encoded)
        print(self._fsm)

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

    @property
    def form(self):
        print(self.morphemeFSM)
        return next(self.formFSM.keys())

    morphemeGetter = (FSM(SIGMA).cross("").star() +
                        FSM("#").cross("") +
                        FSM(SIGMA).star())

    formGetter = (~(FSM("{") | FSM("}")).star())

    @property
    def morphemeFSM(self):
        return (self._fsm @ Item.morphemeGetter).project(side="bottom")

    @property
    def formFSM(self):
        return (self._fsm @ 
                Item.morphemeGetter @ 
                Item.formGetter.star()).project(side="bottom")

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





